#include "Topology.h"

module TeenC {
  uses interface Boot;
  uses interface AMSend;
  uses interface Receive;
  uses interface Packet;
  uses interface AMPacket;
  uses interface SplitControl as RadioControl;
  uses interface Timer<TMilli> as RoundTimer;
  uses interface Timer<TMilli> as AdvertiseTimer;
  uses interface Timer<TMilli> as ScheduleTimer;
  uses interface Timer<TMilli> as DataTimer;
  uses interface Timer<TMilli> as ReportTimer;
  uses interface Timer<TMilli> as SnapshotTimer;
  uses interface Random;
}
implementation {
  enum {
    MSG_START = 1,
    MSG_ADVERTISE = 2,
    MSG_JOIN = 3,
    MSG_SCHEDULE = 4,
    MSG_DATA = 5,
    MSG_FORWARD = 6,
    CTRL_BITS = 200,
    DATA_BITS = 4000,
    ROUND_MS = 5000,
    HT = 30,
    ST = 2
  };

#define E_ELEC 50e-9
#define E_FS 10e-12
#define E_MP 0.0013e-9
#define D0_SQUARED (E_FS / E_MP)

  typedef nx_struct teen_message {
    nx_uint8_t type;
    nx_uint16_t round;
    nx_uint16_t source;
    nx_uint16_t value;
  } teen_message_t;

  message_t packet;
  bool busy = FALSE;
  bool isHead = FALSE;
  bool hasBeenHead = FALSE;
  bool hasSensedValue = FALSE;
  uint16_t clusterHead = 0;
  uint16_t currentRound = 0;
  uint16_t lastHeadRound = 0;
  uint16_t lastSensedValue = 0;
  uint16_t receivedData = 0;
  float energy = 0.5;

  float square(float value) {
    return value * value;
  }

  float distanceSquared(uint16_t first, uint16_t second) {
    float dx = TEEN_X[first] - TEEN_X[second];
    float dy = TEEN_Y[first] - TEEN_Y[second];
    return square(dx) + square(dy);
  }

  float transmitEnergy(uint16_t bits, uint16_t destination) {
    float d2;
    if (destination == AM_BROADCAST_ADDR) {
      d2 = D0_SQUARED;
    } else {
      d2 = distanceSquared(TOS_NODE_ID, destination);
    }
    if (d2 < D0_SQUARED) {
      return E_ELEC * bits + E_FS * bits * d2;
    }
    return E_ELEC * bits + E_MP * bits * d2 * d2;
  }

  void sendMessage(uint8_t type, uint16_t destination, uint16_t value) {
    teen_message_t* payload;
    error_t result;
    uint16_t bits = (type == MSG_DATA || type == MSG_FORWARD) ?
      DATA_BITS : CTRL_BITS;

    if (busy || energy <= 0) {
      return;
    }
    payload = call Packet.getPayload(&packet, sizeof(teen_message_t));
    if (payload == NULL) {
      return;
    }
    payload->type = type;
    payload->round = currentRound;
    payload->source = TOS_NODE_ID;
    payload->value = value;
    result = call AMSend.send(destination, &packet, sizeof(teen_message_t));
    if (result == SUCCESS) {
      busy = TRUE;
      energy -= transmitEnergy(bits, destination);
      if (type == MSG_ADVERTISE || type == MSG_JOIN || type == MSG_SCHEDULE) {
        dbg("TEEN", "CTRL %u %u\n", currentRound, type);
      }
      if (type == MSG_DATA) {
        dbg("TEEN", "SENT %u\n", currentRound);
      }
    }
  }

  void electHead() {
    uint16_t period = 20;
    uint16_t draw;
    float threshold;
    uint16_t elapsed = currentRound - lastHeadRound;

    if ((hasBeenHead && elapsed < period) || energy <= 0) {
      return;
    }
    threshold = 0.05 / (1.0 - 0.05 * (currentRound % period));
    draw = call Random.rand16() % 10000;
    if (draw < threshold * 10000) {
      isHead = TRUE;
      clusterHead = TOS_NODE_ID;
      lastHeadRound = currentRound;
      hasBeenHead = TRUE;
      call AdvertiseTimer.startOneShot(20 + TOS_NODE_ID % TEEN_NODE_COUNT);
      call ScheduleTimer.startOneShot(1400 + TOS_NODE_ID % TEEN_NODE_COUNT);
    }
  }

  void logEnergy() {
    uint32_t nanoJoules = TOS_NODE_ID != 0 && energy > 0 ?
      energy * 1e9 : 0;
    dbg("TEEN", "ENERGY %u %u %u\n",
      currentRound, TOS_NODE_ID, (unsigned int)nanoJoules);
  }

  event void Boot.booted() {
    if (TOS_NODE_ID == 0) {
      energy = 1e9;
    }
    call RadioControl.start();
  }

  event void RadioControl.startDone(error_t error) {
    if (error != SUCCESS) {
      dbg("TEEN", "ERROR radio-start %u\n", TOS_NODE_ID);
      return;
    }
    if (TOS_NODE_ID == 0) {
      call RoundTimer.startPeriodic(ROUND_MS);
    }
  }

  event void RadioControl.stopDone(error_t error) { }

  event void RoundTimer.fired() {
    teen_message_t* payload;

    if (currentRound >= TEEN_ROUNDS) {
      call RoundTimer.stop();
      return;
    }
    currentRound++;
    call SnapshotTimer.startOneShot(4800);
    if (!busy && energy > 0) {
      payload = call Packet.getPayload(&packet, sizeof(teen_message_t));
      if (payload != NULL) {
        payload->type = MSG_START;
        payload->round = currentRound;
        payload->source = 0;
        payload->value = 0;
        if (call AMSend.send(AM_BROADCAST_ADDR, &packet,
            sizeof(teen_message_t)) == SUCCESS) {
          busy = TRUE;
          energy -= transmitEnergy(CTRL_BITS, AM_BROADCAST_ADDR);
        }
      }
    }
  }

  event void AdvertiseTimer.fired() {
    if (isHead) {
      sendMessage(MSG_ADVERTISE, AM_BROADCAST_ADDR, 0);
    } else if (clusterHead != 0) {
      sendMessage(MSG_JOIN, clusterHead, 0);
    }
  }

  event void ScheduleTimer.fired() {
    if (isHead) {
      sendMessage(MSG_SCHEDULE, AM_BROADCAST_ADDR, 0);
    }
  }

  event void DataTimer.fired() {
    uint16_t value;
    bool eventActive;

    if (TOS_NODE_ID == 0 || isHead || clusterHead == 0 || energy <= 0) {
      return;
    }
    eventActive = ((currentRound % 100) < 25) &&
      (distanceSquared(TOS_NODE_ID, 0) < 100 * 100);
    if (eventActive) {
      value = 3500 + call Random.rand16() % 150;
    } else {
      value = 2150 + call Random.rand16() % 150;
    }
    if (value >= HT * 100 &&
        (!hasSensedValue ||
         (value > lastSensedValue ? value - lastSensedValue :
          lastSensedValue - value) >= ST * 100)) {
      hasSensedValue = TRUE;
      lastSensedValue = value;
      sendMessage(MSG_DATA, clusterHead, value);
    }
  }

  event void ReportTimer.fired() {
    if (isHead && receivedData > 0 && energy > 0) {
      sendMessage(MSG_FORWARD, 0, receivedData);
    }
  }

  event void SnapshotTimer.fired() {
    logEnergy();
  }

  event void AMSend.sendDone(message_t* message, error_t error) {
    if (message == &packet) {
      busy = FALSE;
      if (error != SUCCESS) {
        dbg("TEEN", "ERROR send %u %u\n", currentRound, TOS_NODE_ID);
      }
    }
  }

  event message_t* Receive.receive(message_t* message, void* data, uint8_t length) {
    teen_message_t* incoming = data;
    uint16_t sender;
    uint16_t bits;

    if (length < sizeof(teen_message_t)) {
      return message;
    }
    sender = call AMPacket.source(message);
    bits = (incoming->type == MSG_DATA || incoming->type == MSG_FORWARD) ?
      DATA_BITS : CTRL_BITS;
    if (energy > 0) {
      energy -= E_ELEC * bits;
    }
    if (incoming->type != MSG_START && incoming->type != MSG_ADVERTISE &&
        incoming->type != MSG_SCHEDULE && call Random.rand16() % 100 < 2) {
      return message;
    }

    if (incoming->type == MSG_START && TOS_NODE_ID != 0) {
      currentRound = incoming->round;
      isHead = FALSE;
      clusterHead = 0;
      receivedData = 0;
      call DataTimer.startOneShot(2200 + (TOS_NODE_ID % 300) * 3);
      call ReportTimer.startOneShot(4200 + TOS_NODE_ID % TEEN_NODE_COUNT);
      call SnapshotTimer.startOneShot(4800);
      electHead();
    } else if (incoming->type == MSG_ADVERTISE &&
        TOS_NODE_ID != 0 && !isHead && clusterHead == 0) {
      clusterHead = sender;
      call AdvertiseTimer.startOneShot(10 + (TOS_NODE_ID %
        TEEN_NODE_COUNT) * 2);
    } else if (incoming->type == MSG_JOIN && isHead) {
      return message;
    } else if (incoming->type == MSG_DATA && isHead) {
      receivedData++;
    } else if (incoming->type == MSG_FORWARD && TOS_NODE_ID == 0) {
      dbg("TEEN", "RECEIVED %u %u\n", incoming->round, incoming->value);
    }
    return message;
  }
}
