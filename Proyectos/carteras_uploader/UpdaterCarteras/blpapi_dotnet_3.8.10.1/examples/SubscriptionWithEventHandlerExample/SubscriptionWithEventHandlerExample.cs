/* Copyright 2012. Bloomberg Finance L.P.
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to
 * deal in the Software without restriction, including without limitation the
 * rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
 * sell copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:  The above
 * copyright notice and this permission notice shall be included in all copies
 * or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
 * FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
 * IN THE SOFTWARE.
 */
using Event = Bloomberglp.Blpapi.Event;
using EventHandler = Bloomberglp.Blpapi.EventHandler;
using Element = Bloomberglp.Blpapi.Element;
using Message = Bloomberglp.Blpapi.Message;
using Name = Bloomberglp.Blpapi.Name;
using Session = Bloomberglp.Blpapi.Session;

using ArrayList = System.Collections.ArrayList;
using Thread = System.Threading.Thread;
using System.Collections.Generic;
using System;
using System.Text;

namespace Bloomberglp.Blpapi.Examples
{

    public class SubscriptionWithEventHandlerExample
    {
        private static readonly Name SLOW_CONSUMER_WARNING 
            = Name.GetName("SlowConsumerWarning");
        private static readonly Name SLOW_CONSUMER_WARNING_CLEARED 
            = Name.GetName("SlowConsumerWarningCleared");
        private static readonly Name DATA_LOSS = Name.GetName("DataLoss");
        private static readonly Name SUBSCRIPTION_TERMINATED 
            = Name.GetName("SubscriptionTerminated");
        private static readonly Name SOURCE = Name.GetName("source");

        private SessionOptions d_sessionOptions;
        private Session d_session;
        private List<string> d_hosts;
        private int d_port;
        private List<string> d_topics;
        private List<string> d_fields;
        private List<string> d_options;
        private List<Subscription> d_subscriptions;
        private bool d_isSlow;
        private bool d_isStopped;
        private List<Subscription> d_pendingSubscriptions;
        private Dictionary<CorrelationID, object> d_pendingUnsubscribe;
        private object d_lock;

        public static void Main(string[] args)
        {
            System.Console.WriteLine("Realtime Event Handler Example");
            SubscriptionWithEventHandlerExample example =
                new SubscriptionWithEventHandlerExample();
            example.run(args);
        }

        public SubscriptionWithEventHandlerExample()
        {
            d_sessionOptions = new SessionOptions();

            d_sessionOptions.DefaultSubscriptionService = "//blp/mktdata";
            d_sessionOptions.MaxEventQueueSize = 10000;

            d_port = 8194;
            d_hosts = new List<string>();
            d_topics = new List<string>();
            d_fields = new List<string>();
            d_options = new List<string>();
            d_subscriptions = new List<Subscription>();
            d_isSlow = false;
            d_isStopped = false;
            d_pendingSubscriptions = new List<Subscription>();
            d_pendingUnsubscribe = new Dictionary<CorrelationID, object>();
            d_lock = new object();
        }

        private bool createSession()
        {
            if (d_session != null) d_session.Stop();

            System.Console.WriteLine("Connecting to port " + d_port + " on ");
            foreach (string host in d_hosts)
            {
                System.Console.Write(host + " ");
            }
            System.Console.WriteLine();

            d_session = new Session(d_sessionOptions, 
                                    new EventHandler(processEvent));
            if (!d_session.Start())
            {
                System.Console.WriteLine("Failed to start session");
                return false;
            }
            return true;
        }

        private void run(string[] args)
        {
            if (!parseCommandLine(args)) return;

            if (!createSession()) return;

            System.Console.WriteLine("Connected successfully\n");

            if (!d_session.OpenService(
                        d_sessionOptions.DefaultSubscriptionService))
            {
                System.Console.Error.WriteLine(
                    "Failed to open service {0}",
                    d_sessionOptions.DefaultSubscriptionService);
                d_session.Stop();
                return;
            }

            System.Console.WriteLine("Subscribing...\n");
            d_session.Subscribe(d_subscriptions);

            // wait for enter key to exit application
            System.Console.Read();

            lock (d_lock)
            {
                d_isStopped = true;
            }
            d_session.Stop();
            System.Console.WriteLine("Exiting.");
        }

        public void processEvent(Event eventObj, Session session)
        {
            try
            {
                switch (eventObj.Type)
                {
                    case Event.EventType.SUBSCRIPTION_DATA:
                        processSubscriptionDataEvent(eventObj, session);
                        break;
                    case Event.EventType.SUBSCRIPTION_STATUS:
                        lock (d_lock)
                        {
                            processSubscriptionStatus(eventObj, session);
                        }
                        break;
                    case Event.EventType.ADMIN:
                        lock (d_lock)
                        {
                            processAdminEvent(eventObj, session);
                        }
                        break;
                    default:
                        processMiscEvents(eventObj, session);
                        break;
                }
            }
            catch (System.Exception e)
            {
                System.Console.WriteLine(e.ToString());
            }
        }

        private void processSubscriptionStatus(Event eventObj, Session session)
        {
            System.Console.WriteLine("Processing SUBSCRIPTION_STATUS");
            List<Subscription> subscriptionList = null;
            foreach (Message msg in eventObj)
            {
                CorrelationID cid = msg.CorrelationID;
                string topic = (string)cid.Object;
                System.Console.WriteLine(
                    "{0}: {1}",
                    System.DateTime.Now.ToString("s"),
                    topic);
                System.Console.WriteLine(msg);

                if (msg.MessageType == SUBSCRIPTION_TERMINATED
                        && d_pendingUnsubscribe.Remove(cid))
                {
                    // If this message was due to a previous unsubscribe
                    Subscription subscription = getSubscription(cid);
                    if (d_isSlow)
                    {
                        System.Console.WriteLine(
                            "Deferring subscription for topic = {0} because"
                                + " session is slow.",
                            topic);
                        d_pendingSubscriptions.Add(subscription);
                    }
                    else
                    {
                        if (subscriptionList == null)
                        {
                            subscriptionList = new List<Subscription>();
                        }
                        subscriptionList.Add(subscription);
                    }
                }
            }

            if (subscriptionList != null && !d_isStopped)
            {
                session.Subscribe(subscriptionList);
            }
        }

        private void processSubscriptionDataEvent(Event eventObj, 
                                                  Session session)
        {
            System.Console.WriteLine("Processing SUBSCRIPTION_DATA");
            foreach (Message msg in eventObj)
            {
                string topic = (string)msg.CorrelationID.Object;
                System.Console.WriteLine(
                    "{0}: {1}",
                    System.DateTime.Now.ToString("s"),
                    topic);
                System.Console.WriteLine(msg);
            }
        }

        private void processAdminEvent(Event eventObj, Session session)
        {
            System.Console.WriteLine("Processing ADMIN");
            List<CorrelationID> cidsToCancel = null;
            bool previouslySlow = d_isSlow;
            foreach (Message msg in eventObj)
            {
                // An admin event can have more than one messages.
                if (msg.MessageType == SLOW_CONSUMER_WARNING)
                {
                    System.Console.WriteLine(msg);
                    d_isSlow = true;
                }
                else if (msg.MessageType == SLOW_CONSUMER_WARNING_CLEARED)
                {
                    System.Console.WriteLine(msg);
                    d_isSlow = false;
                }
                else if (msg.MessageType == DATA_LOSS)
                {
                    CorrelationID cid = msg.CorrelationID;
                    string topic = (string) cid.Object;
                    System.Console.WriteLine(
                        "{0}: {1}",
                        System.DateTime.Now.ToString("s"),
                        topic);
                    System.Console.WriteLine(msg);
                    if (msg.HasElement(SOURCE))
                    {
                        string sourceStr = msg.GetElementAsString(SOURCE);
                        if (sourceStr.CompareTo("InProc") == 0
                                && !d_pendingUnsubscribe.ContainsKey(cid))
                        {
                            // DataLoss was generated "InProc". This can only
                            // happen if applications are processing events
                            // slowly and hence are not able to keep-up with
                            // the incoming events.
                            if (cidsToCancel == null)
                            {
                                cidsToCancel = new List<CorrelationID>();
                            }
                            cidsToCancel.Add(cid);
                            d_pendingUnsubscribe.Add(cid, null);
                        }
                    }
                }
            }

            if (!d_isStopped)
            {
                if (cidsToCancel != null)
                {
                    session.Cancel(cidsToCancel);
                }
                else if ((previouslySlow && !d_isSlow) 
                             && d_pendingSubscriptions.Count > 0)
                {
                    // Session was slow but is no longer slow. subscribe to any
                    // topics for which we have previously received
                    // SUBSCRIPTION_TERMINATED
                    System.Console.WriteLine(
                        "Subscribing to topics - {0}",
                        getTopicsString(d_pendingSubscriptions));
                    session.Subscribe(d_pendingSubscriptions);
                    d_pendingSubscriptions.Clear();
                }
            }
        }

        private void processMiscEvents(Event eventObj, Session session)
        {
            System.Console.WriteLine("Processing {0}", eventObj.Type);
            foreach (Message msg in eventObj)
            {
                System.Console.WriteLine(
                    "{0}; {1}",
                    System.DateTime.Now.ToString("s"),
                    msg.MessageType + "\n");
            }
        }

        private Subscription getSubscription(CorrelationID cid)
        {
            foreach (Subscription subscription in d_subscriptions)
            {
                if (subscription.CorrelationID.Equals(cid))
                {
                    return subscription;
                }
            }
            throw new KeyNotFoundException(
                    "No subscription found corresponding to cid = " 
                        + cid.ToString());
        }

        private string getTopicsString(List<Subscription> list)
        {
            StringBuilder strBuilder = new StringBuilder();
            for (int count = 0; count < list.Count; ++count)
            {
                Subscription subscription = list[count];
                if (count != 0)
                {
                    strBuilder.Append(", ");
                }
                strBuilder.Append((string) subscription.CorrelationID.Object);
            }
            return strBuilder.ToString();
        }

        private bool parseCommandLine(string[] args)
        {
            for (int i = 0; i < args.Length; ++i)
            {
                if (string.Compare(args[i], "-t", true) == 0 
                        && i + 1 < args.Length)
                {
                    d_topics.Add(args[++i]);
                }
                else if (string.Compare(args[i], "-f", true) == 0 
                             && i + 1 < args.Length)
                {
                    d_fields.Add(args[++i]);
                }
                else if (string.Compare(args[i], "-o", true) == 0 
                             && i + 1 < args.Length)
                {
                    d_options.Add(args[++i]);
                }
                else if (string.Compare(args[i], "-s", true) == 0 
                             && i + 1 < args.Length)
                {
                    d_sessionOptions.DefaultSubscriptionService = args[++i];
                }
                else if (string.Compare(args[i], "-ip", true) == 0 
                             && i + 1 < args.Length)
                {
                    d_hosts.Add(args[++i]);
                }
                else if (string.Compare(args[i], "-p", true) == 0 
                             && i + 1 < args.Length)
                {
                    d_port = int.Parse(args[++i]);
                }
                else if (string.Compare(args[i], "-qsize", true) == 0 
                             && i + 1 < args.Length)
                {
                    d_sessionOptions.MaxEventQueueSize = int.Parse(args[++i]);
                }
                else
                {
                    printUsage();
                    return false;
                }
            }

            if (d_hosts.Count == 0)
            {
                d_hosts.Add("localhost");
            }

            if (d_fields.Count == 0)
            {
                d_fields.Add("LAST_PRICE");
            }

            if (d_topics.Count == 0)
            {
                d_topics.Add("IBM US Equity");
            }

            SessionOptions.ServerAddress[] servers 
                = new SessionOptions.ServerAddress[d_hosts.Count];
            for (int i = 0; i < d_hosts.Count; ++i)
            {
                servers[i] = new SessionOptions.ServerAddress(d_hosts[i], 
                                                              d_port);
            }
            d_sessionOptions.ServerAddresses = servers;
            d_sessionOptions.AutoRestartOnDisconnection = true;
            d_sessionOptions.NumStartAttempts = (d_hosts.Count > 1) ? 1 : 1000;
                // If only one host is provided, make many attempts to connect.
                // When multiple hosts are provided, it's expected that at
                // least one will be up and reachable at any given time, so
                // only try to connect to each server once.

            foreach (string topic in d_topics)
            {
                d_subscriptions.Add(new Subscription(
                    topic, d_fields, d_options, new CorrelationID(topic)));
            }

            return true;
        }

        private void printUsage()
        {
            System.Console.WriteLine(
                    "Usage:\n"
                  + "  Retrieve realtime data\n"
                  + "      [-ip        <ipAddress  = localhost>\n"
                  + "      [-p         <tcpPort    = 8194>\n"
                  + "      [-s         <service    = //blp/mktdata>\n"
                  + "      [-t         <topic      = IBM US Equity>\n"
                  + "      [-f         <field      = LAST_PRICE>\n"
                  + "      [-o         <subscriptionOptions>\n"
                  + "      [-qsize     <qsize      = 10000>\n"
                  + "Press ENTER to quit");
        }
    }
}
