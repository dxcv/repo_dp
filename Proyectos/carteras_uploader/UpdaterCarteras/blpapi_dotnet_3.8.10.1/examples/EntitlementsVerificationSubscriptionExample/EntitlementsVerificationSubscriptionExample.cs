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
using System;
using ArrayList = System.Collections.ArrayList;
using Session = Bloomberglp.Blpapi.Session;
using Name = Bloomberglp.Blpapi.Name;
using Event = Bloomberglp.Blpapi.Event;
using Message = Bloomberglp.Blpapi.Message;
using Service = Bloomberglp.Blpapi.Service;
using Identity = Bloomberglp.Blpapi.Identity;
using Request = Bloomberglp.Blpapi.Request;
using Element = Bloomberglp.Blpapi.Element;
using EventHandler = Bloomberglp.Blpapi.EventHandler;
using SessionOptions = Bloomberglp.Blpapi.SessionOptions;
using CorrrelationID = Bloomberglp.Blpapi.CorrelationID;
using EventQueue = Bloomberglp.Blpapi.EventQueue;
using System.Collections.Generic;

namespace Bloomberglp.Blpapi.Examples
{
	/// <summary>
	/// Summary description for EntitlementsVerificationSubscriptionExample.
	/// </summary>
	public class EntitlementsVerificationSubscriptionExample
	{
		private String d_host;
		private int d_port;
		private String d_field;
		private Name d_fieldAsName;
		private List<string> d_securities;
		private List<int> d_uuids;
		private List<Identity> d_identities;
		private List<string> d_programAddresses;

		private Session d_session;
		private Service d_apiAuthSvc;
		private Service d_blpRefDataSvc;
		private System.Collections.Generic.List<Subscription> d_subscriptions;

		private Name EID = Name.GetName("EID");
		private const String API_AUTH_SVC_NAME = "//blp/apiauth";
		private const String MKT_DATA_SVC_NAME = "//blp/mktdata";

		public static void Main(String[] args)
		{
			System.Console.WriteLine("Entitlements Verification Subscription Example");
			EntitlementsVerificationSubscriptionExample example =
				new EntitlementsVerificationSubscriptionExample();
			example.run(args);
		}

		public EntitlementsVerificationSubscriptionExample()
		{
			d_host = "localhost";
			d_port = 8194;
			d_field = "BEST_BID1";
			d_fieldAsName = Name.GetName(d_field);

			d_securities = new List<string>();
			d_uuids = new List<int>();
			d_identities = new List<Identity>();
			d_programAddresses = new List<string>();
			d_subscriptions = new System.Collections.Generic.List<Subscription>();
		}

		private void run(String[] args)
		{
			if (!parseCommandLine(args))
				return;

			createSession();
			OpenServices();

			// Authorize all the users that are interested in receiving data
			authorizeUsers();

			// Make the various requests that we need to make
			d_session.Subscribe(d_subscriptions);

			// wait for enter key to exit application
			System.Console.Read();

			d_session.Stop();
			System.Console.WriteLine("Exiting.");
		}

		private void createSession()
		{
			SessionOptions options = new SessionOptions();
			options.ServerHost = d_host;
			options.ServerPort = d_port;

			System.Console.WriteLine("Connecting to " + d_host + ":" + d_port);

			d_session = new Session(options, new EventHandler(this.processEvent));
			bool sessionStarted = d_session.Start();
			if (!sessionStarted)
			{
				System.Console.WriteLine("Failed to start session. Exiting...");
				System.Environment.Exit(-1);
			}
		}

		private void OpenServices()
		{
			if (!d_session.OpenService(API_AUTH_SVC_NAME))
			{
				System.Console.WriteLine("Failed to open service: " + API_AUTH_SVC_NAME);
				System.Environment.Exit(-1);
			}

			if (!d_session.OpenService(MKT_DATA_SVC_NAME))
			{
				System.Console.WriteLine("Failed to open service: " + MKT_DATA_SVC_NAME);
				System.Environment.Exit(-2);
			}

			d_apiAuthSvc = d_session.GetService(API_AUTH_SVC_NAME);
			d_blpRefDataSvc = d_session.GetService(MKT_DATA_SVC_NAME);
		}

		public void processSubscriptionDataEvent(Event eventObj, Session session)
		{
			foreach (Message msg in eventObj)
			{
				if (!msg.HasElement(d_fieldAsName)) continue;
				string topic = (string)msg.CorrelationID.Object;
				System.Console.WriteLine(System.DateTime.Now.ToString("s")
					+ ": " + topic + " - " + msg.MessageType);
				Element field = msg.GetElement(d_fieldAsName);
				if (field.IsNull)
				{
					System.Console.WriteLine(d_field + "is null, ignoring");
				}
				Service service = msg.Service;
				bool needsEntitlement = msg.HasElement(EID);
				for (int j = 0; j < d_identities.Count; ++j)
				{
					Identity identity = (Identity)d_identities[j];
					if (!needsEntitlement ||
						identity.HasEntitlements(msg.GetElement(EID), service))
					{
						System.Console.WriteLine("User: " + d_uuids[j] +
							" is entitled to " + field);
						// Now Distribute message to the user. 
					}
					else
					{
						System.Console.WriteLine("User: " + d_uuids[j] +
							" is NOT entitled for " + d_field + " because of " +
							msg.GetElement(EID));
					}
				}
			}
		}

		public void processEvent(Event eventObj, Session session)
		{
			try
			{
				switch (eventObj.Type)
				{
					case Event.EventType.SESSION_STATUS:
					case Event.EventType.SERVICE_STATUS:
					case Event.EventType.REQUEST_STATUS:
					case Event.EventType.AUTHORIZATION_STATUS:
						printEvent(eventObj);
						break;

					case Event.EventType.SUBSCRIPTION_DATA:
						processSubscriptionDataEvent(eventObj, session);
						break;
				}
			}
			catch (System.Exception e)
			{
				System.Console.WriteLine(e.ToString());
			}
		}

		private void authorizeUsers()
		{
			// Authorize each of the users
			for (int i = 0; i < d_uuids.Count; ++i)
			{
				Identity identity = d_session.CreateIdentity();
				d_identities.Add(identity);

				Request authRequest = d_apiAuthSvc.CreateAuthorizationRequest();

				authRequest.Set("uuid", d_uuids[i]);
				authRequest.Set("ipAddress", d_programAddresses[i]);

				CorrelationID correlator = new CorrelationID(i);
				EventQueue eventQueue = new EventQueue();
				d_session.SendAuthorizationRequest(authRequest, identity,
					eventQueue, correlator);

				Event eventObj = eventQueue.NextEvent();
				while (true)
				{
					printEvent(eventObj);
					if (eventObj.Type == Event.EventType.RESPONSE ||
						eventObj.Type == Event.EventType.PARTIAL_RESPONSE ||
						eventObj.Type == Event.EventType.REQUEST_STATUS)
					{
						break;
					}
					eventObj = eventQueue.NextEvent();
				}

			}
		}

		private bool parseCommandLine(String[] args)
		{
			for (int i = 0; i < args.Length; ++i)
			{
				if (string.Compare(args[i], "-s", true) == 0)
				{
					d_securities.Add(args[i + 1]);
				}
				else if (string.Compare(args[i], "-f", true) == 0)
				{
					d_field = args[i + 1];
					d_fieldAsName = Name.GetName(d_field);
				}
				else if (string.Compare(args[i], "-c", true) == 0)
				{
					String credential = args[i + 1];
					int idx = credential.IndexOf(':');
					d_uuids.Add(
						int.Parse(credential.Substring(0, idx)));
					d_programAddresses.Add(credential.Substring(idx + 1));
				}
				else if (string.Compare(args[i], "-ip", true) == 0)
				{
					d_host = args[i + 1];
				}
				else if (string.Compare(args[i], "-p", true) == 0)
				{
					d_port = int.Parse(args[i + 1]);
				}
				else if (string.Compare(args[i], "-h", true) == 0)
				{
					printUsage();
					return false;
				}
			}

			if (d_uuids.Count <= 0)
			{
				System.Console.WriteLine("No uuids were specified");
				return false;
			}

			if (d_uuids.Count != d_programAddresses.Count)
			{
				System.Console.WriteLine("Invalid number of program addresses provided");
			}

			if (d_securities.Count <= 0)
			{
				d_securities.Add("MSFT US Equity");
			}

			foreach (String security in d_securities)
			{
				d_subscriptions.Add(new Subscription(security, d_field, "",
													 new CorrelationID(security)));
			}
			return true;
		}

		private void printUsage()
		{
			System.Console.WriteLine("Usage:");
			System.Console.WriteLine("	Entitlements Verification Subscription example");
			System.Console.WriteLine("		[-s		<security   = MSFT US Equity>]");
			System.Console.WriteLine("		[-f		<field      = BEST_BID1>]");
			System.Console.WriteLine("		[-c		<credential uuid:ipAddress" +
				" eg:12345:10.20.30.40>]");
			System.Console.WriteLine("		[-ip 	<ipAddress  = localhost>]");
			System.Console.WriteLine("		[-p 	<tcpPort    = 8194>]");
			System.Console.WriteLine("Notes:");
			System.Console.WriteLine("Multiple securities and credentials can be" +
				" specified. Only one field can be specified.");

		}

		private void printEvent(Event eventObj)
		{
			foreach (Message msg in eventObj)
			{
				CorrelationID correlationId = msg.CorrelationID;
				if (correlationId != null)
				{
					System.Console.WriteLine("Correlator: " + correlationId);
				}

				Service service = msg.Service;
				if (service != null)
				{
					System.Console.WriteLine("Service: " + service.Name);
				}
				System.Console.WriteLine(msg);
			}
		}

	}
}
