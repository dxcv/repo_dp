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
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading;

namespace Bloomberglp.Blpapi.Examples
{
	public class RequestServiceExample
	{
		private enum AuthorizationStatus
		{
			WAITING,
			AUTHORIZED,
			FAILED
		}

		private enum Role
		{
			SERVER,
			CLIENT,
			BOTH
		}

		private static readonly Name AUTHORIZATION_SUCCESS = Name.GetName("AuthorizationSuccess");
		private static readonly Name TOKEN_SUCCESS = Name.GetName("TokenGenerationSuccess");
		private static readonly Name REFERENCE_DATA_REQUEST = Name.GetName("ReferenceDataRequest");

		private static readonly String AUTH_USER = "AuthenticationType=OS_LOGON";
		private static readonly String AUTH_APP_PREFIX = "AuthenticationMode=APPLICATION_ONLY;ApplicationAuthenticationType=APPNAME_AND_KEY;ApplicationName=";
		private static readonly String AUTH_DIR_PREFIX = "AuthenticationType=DIRECTORY_SERVICE;DirSvcPropertyName=";
		private static readonly String AUTH_OPTION_NONE = "none";
		private static readonly String AUTH_OPTION_USER = "user";
		private static readonly String AUTH_OPTION_APP = "app=";
		private static readonly String AUTH_OPTION_DIR = "dir=";

		private String d_service = "//example/refdata";
		private int d_verbose = 0;
		private List<String> d_hosts = new List<String>();
		private int d_port = 8194;
		private int d_numRetry = 2;

		private String d_authOptions = AUTH_USER;
		private List<String> d_securities = new List<String>();
		private List<String> d_fields = new List<String>();
		private Role d_role = Role.BOTH;
		private Dictionary<CorrelationID, AuthorizationStatus> d_authorizationStatus =
			new Dictionary<CorrelationID, AuthorizationStatus>();

		static double GetTimestamp()
		{
			return ((double)System.DateTime.Now.Ticks) / 10000000;
		}

		private void ProcessServerEvent(Event eventObj, ProviderSession session)
		{
			Console.WriteLine("Server received event " + eventObj.Type);
			if (eventObj.Type == Event.EventType.REQUEST)
			{
				foreach (Message msg in eventObj)
				{
					Console.WriteLine("Message = " + msg);
					if (msg.MessageType == REFERENCE_DATA_REQUEST)
					{
						// Similar to createPublishEvent. We assume just one
						// service - d_service. A responseEvent can only be
						// for single request so we can specify the
						// correlationId - which establishes context -
						// when we create the Event.
						Service service = session.GetService(d_service);
						if (msg.HasElement("timestamp"))
						{
							double requestTime = msg.GetElementAsFloat64("timestamp");
							double latency = GetTimestamp() - requestTime;
							Console.WriteLine("Request latency = " + latency);
						}
						Event response = service.CreateResponseEvent(msg.CorrelationID);
						EventFormatter ef = new EventFormatter(response);

						// In AppendResponse the string is the name of the
						// operation, the correlationId indicates
						// which request we are responding to.
						ef.AppendResponse("ReferenceDataRequest");
						Element securities = msg.GetElement("securities");
						Element fields = msg.GetElement("fields");
						ef.SetElement("timestamp", GetTimestamp());
						ef.PushElement("securityData");
						for (int i = 0; i < securities.NumValues; ++i)
						{
							ef.AppendElement();
							ef.SetElement("security", securities.GetValueAsString(i));
							ef.PushElement("fieldData");
							for (int j = 0; j < fields.NumValues; ++j)
							{
								ef.AppendElement();
								ef.SetElement("fieldId", fields.GetValueAsString(j));
								ef.PushElement("data");
								ef.SetElement("doubleValue", GetTimestamp());
								ef.PopElement();
								ef.PopElement();
							}
							ef.PopElement();
							ef.PopElement();
						}
						ef.PopElement();

						// Service is implicit in the Event. sendResponse has a
						// second parameter - partialResponse -
						// that defaults to false.
						session.SendResponse(response);
					}
				}
			}
			else
			{
				foreach (Message msg in eventObj)
				{
					if (msg.CorrelationID != null && d_verbose > 0)
					{
						Console.WriteLine("cid = " + msg.CorrelationID);
					}
					Console.WriteLine("Message = " + msg);
					if (msg.CorrelationID == null)
					{
						continue;
					}
					lock (d_authorizationStatus)
					{
						if (d_authorizationStatus.ContainsKey(msg.CorrelationID))
						{
							if (msg.MessageType == AUTHORIZATION_SUCCESS)
							{
								d_authorizationStatus[msg.CorrelationID] = AuthorizationStatus.AUTHORIZED;
							}
							else
							{
								d_authorizationStatus[msg.CorrelationID] = AuthorizationStatus.FAILED;
							}
							Monitor.Pulse(d_authorizationStatus);
						}
					}
				}
			}
		}

		private void ProcessClientEvent(Event eventObj, Session session)
		{
			Console.WriteLine("Client received event " + eventObj.Type);
			foreach (Message msg in eventObj)
			{
				if (msg.CorrelationID != null && d_verbose > 1)
				{
					Console.WriteLine("cid = " + msg.CorrelationID);
				}
				Console.WriteLine("Message = " + msg);

				if (msg.CorrelationID == null)
				{
					continue;
				}
				lock (d_authorizationStatus)
				{
					if (d_authorizationStatus.ContainsKey(msg.CorrelationID))
					{
						if (msg.MessageType == AUTHORIZATION_SUCCESS)
						{
							d_authorizationStatus[msg.CorrelationID] = AuthorizationStatus.AUTHORIZED;
						}
						else
						{
							d_authorizationStatus[msg.CorrelationID] = AuthorizationStatus.FAILED;
						}
						Monitor.Pulse(d_authorizationStatus);
					}
				}
			}
		}



		private void PrintUsage()
		{
			Console.WriteLine("Usage:");
			Console.WriteLine("\t[-ip   <ipAddress>]  \tserver name or IP (default: localhost)");
			Console.WriteLine("\t[-p    <tcpPort>]    \tserver port (default: 8194)");
			Console.WriteLine("\t[-t    <number>]     \tnumber of retrying connection on disconnected (default: number of hosts)");
			Console.WriteLine("\t[-v]                 \tincrease verbosity (can be specified more than once)");
			Console.WriteLine("\t[-auth <option>]     \tauthentication option: user|none|app=<app>|dir=<property> (default: user)");
			Console.WriteLine("\t[-s    <security>]   \trequest security for client (default: IBM US Equity)");
			Console.WriteLine("\t[-f    <field>]      \trequest field for client (default: PX_LAST)");
			Console.WriteLine("\t[-r    <option>]     \tservice role option: server|client|both (default: both)");
		}

		private bool ParseCommandLine(String[] args)
		{
			bool numRetryProvidedByUser = false;

			for (int i = 0; i < args.Length; ++i)
			{
				if (string.Compare("-v", args[i], true) == 0)
				{
					++d_verbose;
				}
				else if (string.Compare("-ip", args[i], true) == 0
					&& i + 1 < args.Length)
				{
					d_hosts.Add(args[++i]);
				}
				else if (string.Compare("-p", args[i], true) == 0
					&& i + 1 < args.Length)
				{
					d_port = int.Parse(args[++i]);
				}
				else if (string.Compare("-t", args[i], true) == 0
					&& i + 1 < args.Length)
				{
					d_numRetry = int.Parse(args[++i]);
					numRetryProvidedByUser = true;
				}
				else if (string.Compare("-s", args[i], true) == 0
					&& i + 1 < args.Length)
				{
					d_securities.AddRange(args[++i].Split(','));
				}
				else if (string.Compare("-f", args[i], true) == 0
					&& i + 1 < args.Length)
				{
					d_fields.AddRange(args[++i].Split(','));
				}
				else if (string.Compare("-auth", args[i], true) == 0
					&& i + 1 < args.Length)
				{
					++i;
					if (string.Compare(AUTH_OPTION_NONE, args[i], true) == 0)
					{
						d_authOptions = null;
					}
					else if (string.Compare(AUTH_OPTION_USER, args[i], true)
																	== 0)
					{
						d_authOptions = AUTH_USER;
					}
					else if (string.Compare(AUTH_OPTION_APP, 0, args[i], 0,
										AUTH_OPTION_APP.Length, true) == 0)
					{
						d_authOptions = AUTH_APP_PREFIX
							+ args[i].Substring(AUTH_OPTION_APP.Length);
					}
					else if (string.Compare(AUTH_OPTION_DIR, 0, args[i], 0,
										AUTH_OPTION_DIR.Length, true) == 0)
					{
						d_authOptions = AUTH_DIR_PREFIX
							+ args[i].Substring(AUTH_OPTION_DIR.Length);
					}
					else
					{
						PrintUsage();
						return false;
					}
				}
				else if (string.Compare("-r", args[i], true) == 0
					&& i + 1 < args.Length)
				{
					++i;
					if (string.Compare("server", args[i], true) == 0)
					{
						d_role = Role.SERVER;
					}
					else if (string.Compare("client", args[i], true) == 0)
					{
						d_role = Role.CLIENT;
					}
					else if (string.Compare("both", args[i], true) == 0)
					{
						d_role = Role.BOTH;
					}
					else
					{
						PrintUsage();
						return false;
					}
				}
				else
				{
					PrintUsage();
					return false;
				}
			}

			if (d_hosts.Count == 0)
			{
				d_hosts.Add("localhost");
			}
			if (d_securities.Count == 0)
			{
				d_securities.Add("IBM US Equity");
			}
			if (d_fields.Count == 0)
			{
				d_fields.Add("PX_LAST");
			}
			if (!numRetryProvidedByUser)
			{
				d_numRetry = d_hosts.Count;
			}

			return true;
		}

		void PrintMessage(Event eventObj)
		{
			foreach (Message msg in eventObj)
			{
				Console.WriteLine(msg);
			}
		}

		private bool Authorize(
					Service authService,
					Identity identity,
					AbstractSession session,
					CorrelationID cid)
		{
			lock (d_authorizationStatus)
			{
				d_authorizationStatus[cid] = AuthorizationStatus.WAITING;
			}
			EventQueue tokenEventQueue = new EventQueue();
			try
			{
				session.GenerateToken(new CorrelationID(tokenEventQueue), tokenEventQueue);
			}
			catch (Exception e)
			{
				System.Console.WriteLine(e.Message);
				return false;
			}
			String token = null;
			const int timeoutMilliSeconds = 10000;
			Event eventObj = tokenEventQueue.NextEvent(timeoutMilliSeconds);
			if (eventObj.Type == Event.EventType.TOKEN_STATUS ||
				eventObj.Type == Event.EventType.REQUEST_STATUS)
			{
				foreach (Message msg in eventObj)
				{
					System.Console.WriteLine(msg.ToString());
					if (msg.MessageType == TOKEN_SUCCESS)
					{
						token = msg.GetElementAsString("token");
					}
				}
			}
			if (token == null)
			{
				System.Console.WriteLine("Failed to get token");
				return false;
			}

			Request authRequest = authService.CreateAuthorizationRequest();
			authRequest.Set("token", token);

			lock (d_authorizationStatus)
			{
				session.SendAuthorizationRequest(authRequest, identity, cid);

				long startTime = System.DateTime.Now.Ticks;
				const int WAIT_TIME = 10 * 1000; // 10 seconds
				while (true)
				{
					Monitor.Wait(d_authorizationStatus, WAIT_TIME);
					if (d_authorizationStatus[cid] != AuthorizationStatus.WAITING)
					{
						return d_authorizationStatus[cid] == AuthorizationStatus.AUTHORIZED;
					}
					if (System.DateTime.Now.Ticks - startTime > WAIT_TIME * 10000)
					{
						return false;
					}
				}
			}
		}

		private void ServerRun(ProviderSession providerSession)
		{
			Console.WriteLine("Server is starting------");
			if (!providerSession.Start())
			{
				Console.Error.WriteLine("Failed to start server session");
				return;
			}

			Identity identity = null;
			if (d_authOptions != null)
			{
				bool isAuthorized = false;
				identity = providerSession.CreateIdentity();
				if (providerSession.OpenService("//blp/apiauth"))
				{
					Service authService = providerSession.GetService("//blp/apiauth");
					if (Authorize(authService, identity, providerSession, new CorrelationID()))
					{
						isAuthorized = true;
					}
				}
				if (!isAuthorized)
				{
					Console.Error.WriteLine("No authorization");
					return;
				}
			}

			if (!providerSession.RegisterService(d_service, identity))
			{
				Console.Error.WriteLine("Failed to register " + d_service);
				return;
			}
		}

		private void ClientRun(Session session)
		{
			Console.WriteLine("Client is starting------");
			if (!session.Start())
			{
				Console.Error.WriteLine("Failed to start client session");
				return;
			}

			Identity identity = null;
			if (d_authOptions != null)
			{
				bool isAuthorized = false;
				identity = session.CreateIdentity();
				if (session.OpenService("//blp/apiauth"))
				{
					Service authService = session.GetService("//blp/apiauth");
					if (Authorize(authService, identity, session, new CorrelationID()))
					{
						isAuthorized = true;
					}
				}
				if (!isAuthorized)
				{
					Console.Error.WriteLine("No authorization");
					return;
				}
			}

			if (!session.OpenService(d_service))
			{
				Console.Error.WriteLine("Failed to open " + d_service);
				return;
			}

			Service service = session.GetService(d_service);
			Request request = service.CreateRequest("ReferenceDataRequest");

			// Add securities to request
			Element securities = request.GetElement("securities");
			for (int i = 0; i < d_securities.Count; ++i)
			{
				securities.AppendValue(d_securities[i]);
			}
			// Add fields to request
			Element fields = request.GetElement("fields");
			for (int i = 0; i < d_fields.Count; ++i)
			{
				fields.AppendValue(d_fields[i]);
			}
			// Set time stamp
			request.Set("timestamp", GetTimestamp());

			Console.WriteLine("Sending Request: " + request);
			EventQueue eventQueue = new EventQueue();
			session.SendRequest(request, identity, eventQueue, new CorrelationID());

			while (true)
			{
				Event eventObj = eventQueue.NextEvent();
				Console.WriteLine("Client received an event");
				foreach (Message msg in eventObj)
				{
					if (eventObj.Type == Event.EventType.RESPONSE)
					{
						if (msg.HasElement("timestamp"))
						{
							double responseTime = msg.GetElementAsFloat64("timestamp");
							double latency = GetTimestamp() - responseTime;
							Console.WriteLine("Response latency = " + latency);
						}
					}
					Console.WriteLine(msg);
				}
				if (eventObj.Type == Event.EventType.RESPONSE)
				{
					break;
				}
			}
		}

		public void Run(String[] args)
		{
			if (!ParseCommandLine(args))
				return;

			SessionOptions.ServerAddress[] servers = new SessionOptions.ServerAddress[d_hosts.Count];
			for (int i = 0; i < d_hosts.Count; ++i)
			{
				servers[i] = new SessionOptions.ServerAddress(d_hosts[i], d_port);
			}

			SessionOptions sessionOptions = new SessionOptions();
			sessionOptions.ServerAddresses = servers;
			sessionOptions.AuthenticationOptions = d_authOptions;
			sessionOptions.AutoRestartOnDisconnection = true;
			sessionOptions.NumStartAttempts = d_numRetry;

			Console.Write("Connecting to");
			foreach (SessionOptions.ServerAddress server in sessionOptions.ServerAddresses)
			{
				Console.Write(" " + server);
			}
			Console.WriteLine();

			if (d_role == Role.SERVER || d_role == Role.BOTH)
			{
				ProviderSession session = new ProviderSession(sessionOptions, ProcessServerEvent);
				ServerRun(session);
			}

			if (d_role == Role.CLIENT || d_role == Role.BOTH)
			{
				Session session = new Session(sessionOptions, ProcessClientEvent);
				ClientRun(session);
			}
		}

		public static void Main(String[] args)
		{
			Console.WriteLine("RequestServiceExample");
			RequestServiceExample example = new RequestServiceExample();
			example.Run(args);
			Console.WriteLine("Press ENTER to quit");
			System.Console.Read();
		}
	}
}
