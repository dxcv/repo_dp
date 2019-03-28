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
	/// Summary description for EntitlementsVerificationExample.
	/// </summary>
	public class EntitlementsVerificationExample
	{
		private String d_host;
		private int d_port;
		private List<string> d_securities;
		private List<int> d_uuids;
		private List<Identity> d_identities;
		private List<string> d_programAddresses;

		private Session d_session;
		private Service d_apiAuthSvc;
		private Service d_blpRefDataSvc;

		private static readonly Name RESPONSE_ERROR = Name.GetName("responseError");
		private static readonly Name SECURITY_DATA = Name.GetName("securityData");
		private static readonly Name SECURITY = Name.GetName("security");
		private static readonly Name EID_DATA = Name.GetName("eidData");
		private static readonly Name AUTHORIZATION_REVOKED = Name.GetName(
			"AuthorizationRevoked");
		private static readonly Name ENTITLEMENT_CHANGED = Name.GetName(
			"EntitlementChanged");

		private const String API_AUTH_SVC_NAME = "//blp/apiauth";
		private const String REF_DATA_SVC_NAME = "//blp/refdata";

		public static void Main(String[] args)
		{
			System.Console.WriteLine("Entitlements Verification Example");
			EntitlementsVerificationExample example =
				new EntitlementsVerificationExample();
			example.run(args);
		}

		public EntitlementsVerificationExample()
		{
			d_host = "localhost";
			d_port = 8194;

			d_securities = new List<string>();
			d_uuids = new List<int>();
			d_identities = new List<Identity>();
			d_programAddresses = new List<string>();
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
			sendRefDataRequest();

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

			if (!d_session.OpenService(REF_DATA_SVC_NAME))
			{
				System.Console.WriteLine("Failed to open service: " + REF_DATA_SVC_NAME);
				System.Environment.Exit(-2);
			}

			d_apiAuthSvc = d_session.GetService(API_AUTH_SVC_NAME);
			d_blpRefDataSvc = d_session.GetService(REF_DATA_SVC_NAME);
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
						printEvent(eventObj);
						break;
					case Event.EventType.AUTHORIZATION_STATUS:
						processAuthStatusEvent(eventObj);
						break;
					case Event.EventType.RESPONSE:
					case Event.EventType.PARTIAL_RESPONSE:
						processResponseEvent(eventObj);
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

		private void sendRefDataRequest()
		{
			Request request = d_blpRefDataSvc.CreateRequest(
									"ReferenceDataRequest");

			// Add securities.
			Element securities = request.GetElement("securities");
			for (int i = 0; i < d_securities.Count; ++i)
			{
				securities.AppendValue((String)d_securities[i]);
			}

			// Add fields
			Element fields = request.GetElement("fields");
			fields.AppendValue("PX_LAST");
			fields.AppendValue("DS002");

			request.Set("returnEids", true);

			// Send the request using the server's credentials
			System.Console.WriteLine("Sending RefDataRequest using server " +
				"credentials...");
			d_session.SendRequest(request, null);
		}

		private void processResponseEvent(Event eventObj)
		{
			foreach (Message msg in eventObj)
			{
				if (msg.HasElement(RESPONSE_ERROR))
				{
					System.Console.WriteLine(msg);
					continue;
				}
				// We have a valid response. Distribute it to all the users.
				distributeMessage(msg);
			}
		}

		private void processAuthStatusEvent(Event eventObj)
		{
			foreach (Message msg in eventObj)
			{
				int userid = (int)msg.CorrelationID.Value;
				if (msg.MessageType.Equals(AUTHORIZATION_REVOKED))
				{
					Element errorinfo = msg.GetElement("reason");
					int code = errorinfo.GetElementAsInt32("code");
					String reason = errorinfo.GetElementAsString("message");
					System.Console.WriteLine("Authorization revoked for uuid " +
							   d_uuids[userid] +
							   " with code " + code + " and reason\n\t" + reason);
					/* Reauthorize user here if required, and obtain a new identity.
					 * Existing identity is invalid.
					 */
				}
				else if (msg.MessageType.Equals(ENTITLEMENT_CHANGED))
				{
					System.Console.WriteLine("Entitlements updated for uuid " +
						d_uuids[userid]);
					/* This is just informational.
					 * Continue to use existing identity.
					 */
				}
			}
		}

		private void distributeMessage(Message msg)
		{
			Service service = msg.Service;

			List<int> failedEntitlements = new List<int>();

			Element securities = msg.GetElement(SECURITY_DATA);
			int numSecurities = securities.NumValues;
			System.Console.WriteLine("Processing " + numSecurities + " securities:");
			for (int i = 0; i < numSecurities; ++i)
			{
				Element security = securities.GetValueAsElement(i);
				String ticker = security.GetElementAsString(SECURITY);
				Element entitlements = ((security.HasElement(EID_DATA) ?
					security.GetElement(EID_DATA) : null));

				int numUsers = d_identities.Count;
				if (entitlements != null)
				{
					// Entitlements are required to access this data            	
					for (int j = 0; j < numUsers; ++j)
					{
						failedEntitlements.Clear();
						Identity identity = (Identity)d_identities[j];
						if (identity.HasEntitlements(entitlements, service,
										  failedEntitlements))
						{
							System.Console.WriteLine("User: " + d_uuids[j] +
								" is entitled to get data for: " + ticker);
							// Now Distribute message to the user. 
						}
						else
						{
							System.Console.WriteLine("User: " + d_uuids[j] +
								" is NOT entitled to get data for: " + ticker +
								" - Failed eids: ");
							printFailedEntitlements(failedEntitlements);
						}
					}
				}
				else
				{
					// No Entitlements are required to access this data.
					for (int j = 0; j < numUsers; ++j)
					{
						System.Console.WriteLine("User: " + d_uuids[j] +
							" is entitled to get data for: " + ticker);
						// Now Distribute message to the user. 

					}
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
				d_securities.Add("IBM US Equity");
			}

			return true;
		}

		private void printUsage()
		{
			System.Console.WriteLine("Usage:");
			System.Console.WriteLine("	Entitlements verification example");
			System.Console.WriteLine("		[-s		<security   = IBM US Equity>]");
			System.Console.WriteLine("		[-c		<credential uuid:ipAddress" +
				" eg:12345:10.20.30.40>]");
			System.Console.WriteLine("		[-ip 	<ipAddress  = localhost>]");
			System.Console.WriteLine("		[-p 	<tcpPort    = 8194>]");
			System.Console.WriteLine("Notes:");
			System.Console.WriteLine("Multiple securities and credentials can be" +
				" specified.");

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



		private void printFailedEntitlements(List<int> failedEntitlements)
		{
			int numFailedEntitlements = failedEntitlements.Count;
			for (int i = 0; (i < numFailedEntitlements); ++i)
			{
				System.Console.Write(failedEntitlements[i] + " ");
			}
			System.Console.WriteLine();
		}


	}
}
