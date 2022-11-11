/*
 * Copyright (c) 2022 Universidad de la República - Uruguay
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License version 2 as
 * published by the Free Software Foundation;
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
 *
 * Author: Matías Richart <mrichart@fing.edu.uy>
 */

/**
 * This example program is designed to illustrate the usage of
 * the RealRSSIPropagation Model.
 *
 * This simulation consist of 2 nodes, one AP and one STA.
 * The AP generates UDP CBR traffic to the STA.
 * By default, the AP is at coordinate (0,0,0) and the STA at
 * coordinate (5,0,0) (meters). Both are fixed.
 *
 * The output consists of:
 * - FlowMonitor statistics
 *
 * Example usage:
 *  *
 * To enable the log of rate changes:
 * export NS_LOG=RateAdaptationDistance=level_info
 */

#include "ns3/boolean.h"
#include "ns3/command-line.h"
#include "ns3/config.h"
#include "ns3/gnuplot.h"
#include "ns3/internet-stack-helper.h"
#include "ns3/ipv4-address-helper.h"
#include "ns3/log.h"
#include "ns3/mobility-helper.h"
#include "ns3/mobility-model.h"
#include "ns3/constant-position-mobility-model.h"
#include "ns3/on-off-helper.h"
#include "ns3/packet-sink-helper.h"
#include "ns3/ssid.h"
#include "ns3/uinteger.h"
#include "ns3/yans-wifi-channel.h"
#include "ns3/yans-wifi-helper.h"
#include "ns3/flow-monitor-helper.h"
#include "ns3/double.h"
#include "ns3/ipv4-flow-classifier.h"
#include "ns3/propagation-loss-model.h"

#include "ns3/propagation-delay-model.h"

using namespace ns3;

NS_LOG_COMPONENT_DEFINE("RealRSSITest");

int
main(int argc, char* argv[])
{

    // Simulation parameters. Please don't use double to indicate seconds; use
    // ns-3 Time values which use integers to avoid portability issues.
    
    uint32_t rtsThreshold = 65535;
    int ap_x = 0;
    int ap_y = 0;
    int ap_z = 0;
    
    int sta1_x = 2;
    int sta1_y = 0;      
    int sta1_z = 0;
    
    Time simTime = Seconds (10);
    
    std::string rate = "50Mb/s";
    Time udpAppStartTime = MilliSeconds (500);
    uint32_t udpPacketSize = 1420;
    
    // Where we will store the output files.
    std::string simTag = "default";
    std::string outputDir = "./";

    CommandLine cmd(__FILE__);
    cmd.AddValue("simTime", "Simulation time", simTime);    
    cmd.AddValue("rate", "Transmission rate", rate);
    cmd.AddValue("rtsThreshold", "RTS threshold", rtsThreshold);
    cmd.AddValue("AP_x", "Position of AP in x coordinate", ap_x);
    cmd.AddValue("AP_y", "Position of AP in y coordinate", ap_y);
    cmd.AddValue("AP_z", "Position of AP in z coordinate", ap_z);
    cmd.AddValue("STA1_x", "Position of STA1 in x coordinate", sta1_x);
    cmd.AddValue("STA1_y", "Position of STA1 in y coordinate", sta1_y);
    cmd.AddValue("STA1_z", "Position of STA1 in z coordinate", sta1_z);
    cmd.Parse(argc, argv);

    // Define the APs
    NodeContainer wifiApNodes;
    wifiApNodes.Create(1);

    // Define the STAs
    NodeContainer wifiStaNodes;
    wifiStaNodes.Create(1);

    YansWifiPhyHelper wifiPhy;
    Ptr<YansWifiChannel> channel = CreateObject<YansWifiChannel> ();
    
    ObjectFactory m_propDelay;
    m_propDelay.SetTypeId ("ns3::ConstantSpeedPropagationDelayModel");
    Ptr<PropagationDelayModel> propDelay = m_propDelay.Create<PropagationDelayModel> ();
    
    Ptr<RealRSSIPropagationLossModel> propLoss = CreateObject<RealRSSIPropagationLossModel> ();
    channel->SetPropagationDelayModel (propDelay);
    channel->SetPropagationLossModel (propLoss);
   
    
    wifiPhy.SetChannel(channel);

    NetDeviceContainer wifiApDevices;
    NetDeviceContainer wifiStaDevices;
    NetDeviceContainer wifiDevices;

    WifiHelper wifi;
    wifi.SetStandard(WIFI_STANDARD_80211n);

    WifiMacHelper wifiMac;
    
    // Configure the AP node
    wifi.SetRemoteStationManager("ns3::MinstrelHtWifiManager", "RtsCtsThreshold", UintegerValue(rtsThreshold));
    Ssid ssid = Ssid("AP");
    wifiMac.SetType("ns3::ApWifiMac", "Ssid", SsidValue(ssid));
    wifiApDevices.Add(wifi.Install(wifiPhy, wifiMac, wifiApNodes.Get(0)));

    // Configure the STA node
    wifi.SetRemoteStationManager("ns3::MinstrelHtWifiManager", "RtsCtsThreshold", UintegerValue(rtsThreshold));
    ssid = Ssid("AP");
    wifiMac.SetType("ns3::StaWifiMac", "Ssid", SsidValue(ssid));
    wifiStaDevices.Add(wifi.Install(wifiPhy, wifiMac, wifiStaNodes.Get(0)));

    wifiDevices.Add(wifiStaDevices);
    wifiDevices.Add(wifiApDevices);

    // Configure the mobility.
    MobilityHelper mobility;
    Ptr<ListPositionAllocator> positionAlloc = CreateObject<ListPositionAllocator>();
    
    // Initial position of AP and STA
    positionAlloc->Add(Vector(ap_x, ap_y, ap_z));
    
    positionAlloc->Add(Vector(sta1_x, sta1_y, sta1_z));
    
    mobility.SetPositionAllocator(positionAlloc);
    mobility.SetMobilityModel("ns3::ConstantPositionMobilityModel");
    
    mobility.Install(wifiApNodes.Get(0));
    mobility.Install(wifiStaNodes);
    
    Ptr<MobilityModel> auxMobility = CreateObject<ConstantPositionMobilityModel> ();
    auxMobility->SetPosition (Vector (5.0, 0.0, 0.0));
    propLoss->SetRssi (wifiApNodes.Get (0)->GetObject<MobilityModel> (), auxMobility, -50.0, true);


    // Configure the IP stack
    InternetStackHelper stack;
    stack.Install(wifiApNodes);
    stack.Install(wifiStaNodes);
    Ipv4AddressHelper address;
    address.SetBase("10.1.1.0", "255.255.255.0");
    Ipv4InterfaceContainer i = address.Assign(wifiDevices);
    Ipv4Address sinkAddress = i.GetAddress(0);
    uint16_t port = 9;

    // Configure the CBR generator
    PacketSinkHelper sink("ns3::UdpSocketFactory", InetSocketAddress(sinkAddress, port));
    ApplicationContainer apps_sink = sink.Install(wifiStaNodes.Get(0));

    OnOffHelper onoff("ns3::UdpSocketFactory", InetSocketAddress(sinkAddress, port));
    onoff.SetConstantRate(DataRate (rate), udpPacketSize);
    onoff.SetAttribute("StartTime", TimeValue(udpAppStartTime));
    onoff.SetAttribute("StopTime", TimeValue(simTime));
    ApplicationContainer apps_source = onoff.Install(wifiApNodes.Get(0));

    apps_sink.Start(udpAppStartTime);
    apps_sink.Stop(simTime);

    // Confifure flow monitor

    FlowMonitorHelper flowmonHelper;

    Ptr<ns3::FlowMonitor> monitor = flowmonHelper.InstallAll() ;
    monitor->SetAttribute ("DelayBinWidth", DoubleValue (0.001));
    monitor->SetAttribute ("JitterBinWidth", DoubleValue (0.001));
    monitor->SetAttribute ("PacketSizeBinWidth", DoubleValue (20));

    Simulator::Stop (simTime);
    Simulator::Run ();

    // Print per-flow statistics
    
    monitor->CheckForLostPackets ();
    Ptr<Ipv4FlowClassifier> classifier = DynamicCast<Ipv4FlowClassifier> (flowmonHelper.GetClassifier ());
    FlowMonitor::FlowStatsContainer stats = monitor->GetFlowStats ();

    double averageFlowThroughput = 0.0;
    double averageFlowDelay = 0.0;

    std::ofstream outFile;
    std::string filename = outputDir + "/" + simTag;
    outFile.open (filename.c_str (), std::ofstream::out | std::ofstream::trunc);
    if (!outFile.is_open ())
    {
      std::cerr << "Can't open file " << filename << std::endl;
      return 1;
    }

    outFile.setf (std::ios_base::fixed);

    double flowDuration = (simTime - udpAppStartTime).GetSeconds ();
    for (std::map<FlowId, FlowMonitor::FlowStats>::const_iterator i = stats.begin (); i != stats.end (); ++i)
    {
      Ipv4FlowClassifier::FiveTuple t = classifier->FindFlow (i->first);
      std::stringstream protoStream;
      protoStream << (uint16_t) t.protocol;
      if (t.protocol == 6)
        {
          protoStream.str ("TCP");
        }
      if (t.protocol == 17)
        {
          protoStream.str ("UDP");
        }
      outFile << "Flow " << i->first << " (" << t.sourceAddress << ":" << t.sourcePort << " -> " << t.destinationAddress << ":" << t.destinationPort << ") proto " << protoStream.str () << "\n";
      outFile << "  Tx Packets: " << i->second.txPackets << "\n";
      outFile << "  Tx Bytes:   " << i->second.txBytes << "\n";
      outFile << "  TxOffered:  " << i->second.txBytes * 8.0 / flowDuration / 1000.0 / 1000.0  << " Mbps\n";
      outFile << "  Rx Bytes:   " << i->second.rxBytes << "\n";
      if (i->second.rxPackets > 0)
        {
          // Measure the duration of the flow from receiver's perspective
          averageFlowThroughput += i->second.rxBytes * 8.0 / flowDuration / 1000 / 1000;
          averageFlowDelay += 1000 * i->second.delaySum.GetSeconds () / i->second.rxPackets;

          outFile << "  Throughput: " << i->second.rxBytes * 8.0 / flowDuration / 1000 / 1000  << " Mbps\n";
          outFile << "  Mean delay:  " << 1000 * i->second.delaySum.GetSeconds () / i->second.rxPackets << " ms\n";
          //outFile << "  Mean upt:  " << i->second.uptSum / i->second.rxPackets / 1000/1000 << " Mbps \n";
          outFile << "  Mean jitter:  " << 1000 * i->second.jitterSum.GetSeconds () / i->second.rxPackets  << " ms\n";
        }
      else
        {
          outFile << "  Throughput:  0 Mbps\n";
          outFile << "  Mean delay:  0 ms\n";
          outFile << "  Mean jitter: 0 ms\n";
        }
      outFile << "  Rx Packets: " << i->second.rxPackets << "\n";
    }

    outFile << "\n\n  Mean flow throughput: " << averageFlowThroughput / stats.size () << "\n";
    outFile << "  Mean flow delay: " << averageFlowDelay / stats.size () << "\n";

    outFile.close ();

    std::ifstream f (filename.c_str ());

    if (f.is_open ())
    {
      std::cout << f.rdbuf ();
    }

    Simulator::Destroy ();
    return 0;
}
