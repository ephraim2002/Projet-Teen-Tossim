configuration TeenAppC { }
implementation {
  components MainC, TeenC, ActiveMessageC, new AMSenderC(6) as Sender;
  components new AMReceiverC(6) as Receiver;
  components new TimerMilliC() as RoundTimer;
  components new TimerMilliC() as AdvertiseTimer;
  components new TimerMilliC() as ScheduleTimer;
  components new TimerMilliC() as DataTimer;
  components new TimerMilliC() as ReportTimer;
  components new TimerMilliC() as SnapshotTimer;
  components RandomC;

  TeenC.Boot -> MainC.Boot;
  TeenC.AMSend -> Sender;
  TeenC.Receive -> Receiver;
  TeenC.Packet -> Sender;
  TeenC.AMPacket -> ActiveMessageC;
  TeenC.RadioControl -> ActiveMessageC;
  TeenC.RoundTimer -> RoundTimer;
  TeenC.AdvertiseTimer -> AdvertiseTimer;
  TeenC.ScheduleTimer -> ScheduleTimer;
  TeenC.DataTimer -> DataTimer;
  TeenC.ReportTimer -> ReportTimer;
  TeenC.SnapshotTimer -> SnapshotTimer;
  TeenC.Random -> RandomC;
}
