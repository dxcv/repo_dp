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
using System.Text;
using Bloomberglp.Blpapi;
using System.Collections;
using System.Threading;

namespace Bloomberglp.Blpapi.Examples
{
	public class MktdataPublisherExample
	{
		private const String AUTH_USER = "AuthenticationType=OS_LOGON";
		private const String AUTH_APP_PREFIX = "AuthenticationMode=APPLICATION_ONLY;"
			+ "ApplicationAuthenticationType=APPNAME_AND_KEY;ApplicationName=";
		private const String AUTH_DIR_PREFIX = "AuthenticationType=DIRECTORY_SERVICE;"
			+ "DirSvcPropertyName=";
		private const String AUTH_OPTION_NONE = "none";
		private const String AUTH_OPTION_USER = "user";
		private const String AUTH_OPTION_APP = "app=";
		private const String AUTH_OPTION_DIR = "dir=";

		private static readonly Name SERVICE_REGISTERED = Name.GetName("ServiceRegistered");
		private static readonly Name SERVICE_REGISTER_FAILURE
			= Name.GetName("ServiceRegisterFailure");
		private static readonly Name TOPIC_SUBSCRIBED = Name.GetName("TopicSubscribed");
		private static readonly Name TOPIC_UNSUBSCRIBED = Name.GetName("TopicUnsubscribed");
		private static readonly Name TOPIC_CREATED = Name.GetName("TopicCreated");
		private static readonly Name TOPIC_RECAP = Name.GetName("TopicRecap");
		private static readonly Name TOPIC = Name.GetName("topic");
		private static readonly Name RESOLUTION_SUCCESS = Name.GetName("ResolutionSuccess");
		private static readonly Name RESOLUTION_FAILURE = Name.GetName("ResolutionFailure");
		private static readonly Name PERMISSION_REQUEST = Name.GetName("PermissionRequest");
		private static readonly Name TOKEN_SUCCESS = Name.GetName("TokenGenerationSuccess");
		private static readonly Name TOKEN_FAILURE = Name.GetName("TokenGenerationFailure");
		private static readonly Name AUTHORIZATION_SUCCESS = Name.GetName("AuthorizationSuccess");
		private static readonly Name AUTHORIZATION_FAILURE = Name.GetName("AuthorizationFailure");
		private static readonly Name SESSION_TERMINATED = Name.GetName("SessionTerminated");

		private String d_service = "//viper/mktdata";
		private int d_verbose = 0;
		private List<String> d_hosts = new List<String>();
		private int d_port = 8194;
		private List<int> d_eids = new List<int>();

		private readonly Dictionary<Topic, Topic> d_topicSet = new Dictionary<Topic, Topic>();
		private readonly Dictionary<string, string> d_subscribedTopics
			= new Dictionary<string, string>();
		private bool? d_registerServiceResponse = null;
		private String d_groupId = null;
		private int d_priority = int.MaxValue;

		private String d_authOptions = AUTH_USER;
		private int d_clearInterval = 0;

		private bool d_useSsc = false;
		private int  d_sscBegin;
		private int  d_sscEnd;
		private int  d_sscPriority;

		private int? d_resolveSubServiceCode = null;
		private volatile bool d_running = true;

		enum AuthorizationStatus
		{
			WAITING,
			AUTHORIZED,
			FAILED
		};
		private Dictionary<CorrelationID, AuthorizationStatus> d_authorizationStatus
			= new Dictionary<CorrelationID, AuthorizationStatus>();

		public void ProcessEvent(Event eventObj, ProviderSession session)
		{

			if (d_verbose > 0)
			{
				Console.WriteLine("Received event " + eventObj.Type);
				foreach (Message msg in eventObj)
				{
					Console.WriteLine("cid = " + msg.CorrelationID);
					Console.WriteLine("Message = " + msg);
				}
			}

			if (eventObj.Type == Event.EventType.SESSION_STATUS)
			{
				foreach (Message msg in eventObj)
				{
					if (msg.MessageType == SESSION_TERMINATED)
					{
						d_running = false;
						break;
					}
				}
			}
			else if (eventObj.Type == Event.EventType.TOPIC_STATUS)
			{
				TopicList topicList = new TopicList();
				foreach (Message msg in eventObj)
				{
					if (msg.MessageType == TOPIC_SUBSCRIBED)
					{
						Topic topic = session.GetTopic(msg);
						lock (d_topicSet)
						{
							string topicStr = msg.GetElementAsString(TOPIC);
							d_subscribedTopics[topicStr] = topicStr;
							if (topic == null)
							{
								CorrelationID cid
									= new CorrelationID(msg.GetElementAsString("topic"));
								topicList.Add(msg, cid);
							}
							else
							{
								if (!d_topicSet.ContainsKey(topic))
								{
									d_topicSet[topic] = topic;
									Monitor.PulseAll(d_topicSet);
								}
							}
						}
					}
					else if (msg.MessageType == TOPIC_UNSUBSCRIBED)
					{
						lock (d_topicSet)
						{
							d_subscribedTopics.Remove(msg.GetElementAsString(TOPIC));
							Topic topic = session.GetTopic(msg);
							d_topicSet.Remove(topic);
						}
					}
					else if (msg.MessageType == TOPIC_CREATED)
					{
						Topic topic = session.GetTopic(msg);
						lock (d_topicSet)
						{
							if (d_subscribedTopics.ContainsKey(msg.GetElementAsString(TOPIC))
								&& !d_topicSet.ContainsKey(topic))
							{
								d_topicSet[topic] = topic;
								Monitor.PulseAll(d_topicSet);
							}
						}
					}
					else if (msg.MessageType == TOPIC_RECAP)
					{
						// Here we send a recap in response to a Recap Request.
						Topic topic = session.GetTopic(msg);
						lock (d_topicSet)
						{
							if (!d_topicSet.ContainsKey(topic))
							{
								continue;
							}
						}
						Service service = topic.Service;
						Event recapEvent = service.CreatePublishEvent();
						EventFormatter eventFormatter = new EventFormatter(recapEvent);
						eventFormatter.AppendRecapMessage(topic, msg.CorrelationID);
						eventFormatter.SetElement("OPEN", 100.0);

						session.Publish(recapEvent);
						foreach (Message recapMsg in recapEvent)
						{
							Console.WriteLine(recapMsg);
						}
					}
				}

				// createTopicsAsync will result in RESOLUTION_STATUS, TOPIC_CREATED events.
				if (topicList.Size > 0)
				{
					session.CreateTopicsAsync(topicList);
				}
			}
			else if (eventObj.Type == Event.EventType.SERVICE_STATUS)
			{
				foreach (Message msg in eventObj)
				{
					if (msg.MessageType == SERVICE_REGISTERED)
					{
						Object registerServiceResponseMonitor = msg.CorrelationID.Object;
						lock (registerServiceResponseMonitor)
						{
							d_registerServiceResponse = true;
							Monitor.PulseAll(registerServiceResponseMonitor);
						}
					}
					else if (msg.MessageType == SERVICE_REGISTER_FAILURE)
					{
						Object registerServiceResponseMonitor = msg.CorrelationID.Object;
						lock (registerServiceResponseMonitor)
						{
							d_registerServiceResponse = false;
							Monitor.PulseAll(registerServiceResponseMonitor);
						}
					}
				}
			}
			else if (eventObj.Type == Event.EventType.RESOLUTION_STATUS)
			{
				foreach (Message msg in eventObj)
				{
					if (msg.MessageType == RESOLUTION_SUCCESS)
					{
						String resolvedTopic
							= msg.GetElementAsString(Name.GetName("resolvedTopic"));
						Console.WriteLine("ResolvedTopic: " + resolvedTopic);
					}
					else if (msg.MessageType == RESOLUTION_FAILURE)
					{
						Console.WriteLine(
								"Topic resolution failed (cid = " +
								msg.CorrelationID +
								")");
					}
				}
			}
			else if (eventObj.Type == Event.EventType.REQUEST)
			{
				Service service = session.GetService(d_service);
				foreach (Message msg in eventObj)
				{
					if (msg.MessageType == PERMISSION_REQUEST)
					{
						// Similar to createPublishEvent. We assume just one
						// service - d_service. A responseEvent can only be
						// for single request so we can specify the
						// correlationId - which establishes context -
						// when we create the Event.
						Event response = service.CreateResponseEvent(msg.CorrelationID);
						EventFormatter ef = new EventFormatter(response);
						int permission = 1; // ALLOWED: 0, DENIED: 1
						if (msg.HasElement("uuid"))
						{
							int uuid = msg.GetElementAsInt32("uuid");
							Console.WriteLine("UUID = " + uuid);
							permission = 0;
						}
						if (msg.HasElement("applicationId"))
						{
							int applicationId = msg.GetElementAsInt32("applicationId");
							Console.WriteLine("APPID = " + applicationId);
							permission = 0;
						}
						// In appendResponse the string is the name of the
						// operation, the correlationId indicates
						// which request we are responding to.
						ef.AppendResponse("PermissionResponse");
						ef.PushElement("topicPermissions");
						// For each of the topics in the request, add an entry
						// to the response
						Element topicsElement = msg.GetElement(Name.GetName("topics"));
						for (int i = 0; i < topicsElement.NumValues; ++i)
						{
							ef.AppendElement();
							ef.SetElement("topic", topicsElement.GetValueAsString(i));

							ef.SetElement("result", permission); // ALLOWED: 0, DENIED: 1

							if (permission == 1)
							{
								// DENIED
								ef.PushElement("reason");
								ef.SetElement("source", "My Publisher Name");
								ef.SetElement("category", "NOT_AUTHORIZED");
								// or BAD_TOPIC, or custom

								ef.SetElement("subcategory", "Publisher Controlled");
								ef.SetElement(
									"description",
									"Permission denied by My Publisher Name");
								ef.PopElement();
							}
							else
							{
								// ALLOWED
								if (d_resolveSubServiceCode != null)
								{
									ef.SetElement("subServiceCode",
												  d_resolveSubServiceCode.Value);
									Console.WriteLine(
										String.Format(
											"Mapping topic {0} to "
												+ "subserviceCode {1}",
											topicsElement.GetValueAsString(i),
											d_resolveSubServiceCode));
								} 
								if (d_eids.Count != 0)
								{
									ef.PushElement("permissions");
									ef.AppendElement();
									ef.SetElement("permissionService", "//blp/blpperm");
									ef.PushElement("eids");
									for (int j = 0; j < d_eids.Count; ++j)
									{
										ef.AppendValue(d_eids[j]);
									}
									ef.PopElement();
									ef.PopElement();
									ef.PopElement();
								}
							}
							ef.PopElement();
						}
						ef.PopElement();
						// Service is implicit in the Event. sendResponse has a
						// second parameter - partialResponse -
						// that defaults to false.
						session.SendResponse(response);
					}
					else
					{
						Console.WriteLine("Received unknown request: " + msg);
					}
				}
			}
			else if (eventObj.Type == Event.EventType.RESPONSE
				  || eventObj.Type == Event.EventType.PARTIAL_RESPONSE
				  || eventObj.Type == Event.EventType.REQUEST_STATUS)
			{
				foreach (Message msg in eventObj)
				{
					if (msg.CorrelationID != null && d_verbose > 1)
					{
						Console.Out.WriteLine("cid = " + msg.CorrelationID);
					}
					Console.Out.WriteLine("Message = " + msg);

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
								d_authorizationStatus[msg.CorrelationID]
									= AuthorizationStatus.AUTHORIZED;
							}
							else
							{
								d_authorizationStatus[msg.CorrelationID]
									= AuthorizationStatus.FAILED;
							}
							Monitor.Pulse(d_authorizationStatus);
						}
					}
				}
			}
		}

		private void PrintUsage()
		{
			Console.WriteLine("Publish market data.");
			Console.WriteLine("Usage:");
			Console.WriteLine("\t[-ip   <ipAddress>]  \tserver name or IP (default: localhost)");
			Console.WriteLine("\t[-p    <tcpPort>]    \tserver port (default: 8194)");
			Console.WriteLine("\t[-s    <service>]    \tservice name (default: //viper/mktdata)");
			Console.WriteLine("\t[-g    <groupId>]    \tpublisher groupId "
														+ "(defaults to a unique value)");
			Console.WriteLine("\t[-pri  <priority>]   \tpublisher priority "
														+ "(default: Integer.MAX_VALUE)");
			Console.WriteLine("\t[-v]                 \tincrease verbosity "
														+ "(can be specified more than once)");
			Console.WriteLine("\t[-c    <event count>]\tnumber of events after which cache will "
														+ "be cleared (default: 0 i.e cache never "
														+ "cleared)");
			Console.WriteLine(
				"\t[-c    <event count>]\tnumber of events after which cache will "
					+ "be cleared (default: 0 i.e cache never cleared)");
			Console.WriteLine(
				"\t[-ssc  <ssc range>]  \tactive sub-service code option: "
					+ "<begin>,<end>,<priority>");
			Console.WriteLine(
				"\t[-rssc <ssc >]       \tsub-service code to be used in resolve");
			Console.WriteLine("\t[-auth <option>]     \tauthentication option: user|none|"
														+ "app=<app>|userapp=<app>|dir=<property> "
														+ "(default: user)");
		}

		private bool ParseCommandLine(String[] args)
		{
			for (int i = 0; i < args.Length; ++i)
			{
				if (string.Compare("-ip", args[i], true) == 0
						&& i + 1 < args.Length)
				{
					d_hosts.Add(args[++i]);
				}
				else if (string.Compare("-p", args[i], true) == 0
						&& i + 1 < args.Length)
				{
					d_port = int.Parse(args[++i]);
				}
				else if (string.Compare("-s", args[i], true) == 0
						&& i + 1 < args.Length)
				{
					d_service = args[++i];
				}
				else if (string.Compare("-e", args[i], true) == 0
						&& i + 1 < args.Length)
				{
					d_eids.Add(int.Parse(args[++i]));
				}
				else if (string.Compare("-g", args[i], true) == 0
						&& i + 1 < args.Length)
				{
					d_groupId = args[++i];
				}
				else if (string.Compare("-pri", args[i], true) == 0
						&& i + 1 < args.Length)
				{
					d_priority = int.Parse(args[++i]);
				}
				else if (string.Compare("-v", args[i], true) == 0)
				{
					++d_verbose;
				}
				else if (string.Compare("-c", args[i], true) == 0
						&& i + 1 < args.Length)
				{
					d_clearInterval = int.Parse(args[++i]);
				}
				else if (string.Compare("-ssc", args[i], true) == 0
						&& i + 1 < args.Length)
				{
					String[] splitRange = args[++i].Split(',');
					if (splitRange.Length != 3)
					{
						PrintUsage();
						return false;
					}
					d_useSsc = true;
					d_sscBegin = int.Parse(splitRange[0]);
					d_sscEnd = int.Parse(splitRange[1]);
					d_sscPriority = int.Parse(splitRange[2]);
				}
				else if (string.Compare("-rssc", args[i], true) == 0
						&& i + 1 < args.Length)
				{
					d_resolveSubServiceCode = int.Parse(args[++i]);
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
				else if (string.Compare("-h", args[i], true) == 0)
				{
					PrintUsage();
					return false;
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

			return true;
		}

		private void Activate(ProviderSession session) {
		if (d_useSsc) {
			Console.WriteLine(
				String.Format(
					"Activating sub service code range [{0}, {1}] "
						+ "@ priority: {2}",
					d_sscBegin,
					d_sscEnd,
					d_sscPriority));
			session.ActivateSubServiceCodeRange(d_service,
												d_sscBegin,
												d_sscEnd,
												d_sscPriority);
		}
	}

		private void Deactivate(ProviderSession session) {
		if (d_useSsc) {
			Console.WriteLine(
				String.Format(
					"DeActivating sub service code range [{0}, {1}] "
						+ "@ priority: {2}",
					d_sscBegin,
					d_sscEnd,
					d_sscPriority));
			session.DeactivateSubServiceCodeRange(d_service,
												  d_sscBegin,
												  d_sscEnd);
		}
	}
		private bool Authorize(
				Service authService,
				Identity identity,
				ProviderSession session,
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

				DateTime startTime = System.DateTime.Now;
				int waitTime = 10 * 1000; // 10 seconds
				while (true)
				{
					Monitor.Wait(d_authorizationStatus, waitTime);
					if (d_authorizationStatus[cid] != AuthorizationStatus.WAITING)
					{
						return d_authorizationStatus[cid] == AuthorizationStatus.AUTHORIZED;
					}
					waitTime -= (int)(System.DateTime.Now - startTime).TotalMilliseconds;
					if (waitTime <= 0)
					{
						return false;
					}
				}
			}
		}

		public void Run(String[] args)
		{
			if (!ParseCommandLine(args))
				return;

			SessionOptions.ServerAddress[] servers
				= new SessionOptions.ServerAddress[d_hosts.Count];
			for (int i = 0; i < d_hosts.Count; ++i)
			{
				servers[i] = new SessionOptions.ServerAddress(d_hosts[i], d_port);
			}

			SessionOptions sessionOptions = new SessionOptions();
			sessionOptions.ServerAddresses = servers;
			sessionOptions.AuthenticationOptions = d_authOptions;
			sessionOptions.AutoRestartOnDisconnection = true;
			sessionOptions.NumStartAttempts = servers.Length;

			Console.Write("Connecting to");
			foreach (SessionOptions.ServerAddress server in sessionOptions.ServerAddresses)
			{
				Console.Write(" " + server);
			}
			Console.WriteLine();

			ProviderSession session = new ProviderSession(sessionOptions, ProcessEvent);

			if (!session.Start())
			{
				Console.Error.WriteLine("Failed to start session");
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
					System.Console.Error.WriteLine("No authorization");
					return;
				}
			}

			ServiceRegistrationOptions serviceRegistrationOptions
				= new ServiceRegistrationOptions();
			serviceRegistrationOptions.GroupId = d_groupId;
			serviceRegistrationOptions.ServicePriority = d_priority;


			if (d_useSsc) {
				Console.WriteLine(
					String.Format(
						"Activating sub service code range [{0}, {1}] "
							+ "@ priority: {2}",
						d_sscBegin,
						d_sscEnd,
						d_sscPriority));
				try {
					serviceRegistrationOptions.AddActiveSubServiceCodeRange(
						d_sscBegin,
						d_sscEnd,
						d_sscPriority);
				} catch(Exception e) {
					Console.WriteLine(
						"FAILED to add active sub service codes. Exception " + e);
				}
			}

			bool wantAsyncRegisterService = true;
			if (wantAsyncRegisterService)
			{
				Object registerServiceResponseMonitor = new Object();
				CorrelationID registerCID = new CorrelationID(registerServiceResponseMonitor);
				lock (registerServiceResponseMonitor)
				{
					if (d_verbose > 0)
					{
						Console.WriteLine("start registerServiceAsync, cid = " + registerCID);
					}
					session.RegisterServiceAsync(
						d_service,
						identity,
						registerCID,
						serviceRegistrationOptions);
					for (int i = 0; d_registerServiceResponse == null && i < 10; ++i)
					{
						Monitor.Wait(registerServiceResponseMonitor, 1000);
					}
				}
			}
			else
			{
				bool result = session.RegisterService(
					d_service,
					identity,
					serviceRegistrationOptions);
				d_registerServiceResponse = result;
			}

			Service service = session.GetService(d_service);
			if (service != null && d_registerServiceResponse == true)
			{
				Console.WriteLine("Service registered: " + d_service);
			}
			else
			{
				Console.Error.WriteLine("Service registration failed: " + d_service);
				return;
			}

			// Dump schema for the service
			if (d_verbose > 1)
			{
				Console.WriteLine("Schema for service:" + d_service);
				for (int i = 0; i < service.NumEventDefinitions; ++i)
				{
					SchemaElementDefinition eventDefinition = service.GetEventDefinition(i);
					Console.WriteLine(eventDefinition);
				}
			}

			// Now we will start publishing
			int eventCount = 0;
			long tickCount = 1;
			while (d_running)
			{
				Event eventObj;
				lock (d_topicSet)
				{

					if (d_topicSet.Count == 0)
					{
						Monitor.Wait(d_topicSet, 100);
					}

					if (d_topicSet.Count == 0)
					{
						continue;
					}

					eventObj = service.CreatePublishEvent();
					EventFormatter eventFormatter = new EventFormatter(eventObj);

					bool publishNull = false;
					if (d_clearInterval > 0 && eventCount == d_clearInterval)
					{
						eventCount = 0;
						publishNull = true;
					}

					foreach (Topic topic in d_topicSet.Keys)
					{
						if (!topic.IsActive())
						{
							System.Console.WriteLine("[WARNING] Publishing on an inactive topic.");
						}
						eventFormatter.AppendMessage("MarketDataEvents", topic);
						if (publishNull)
						{
							eventFormatter.SetElementNull("HIGH");
							eventFormatter.SetElementNull("LOW");
						}
						else
						{
							++eventCount;
							if (1 == tickCount)
							{
								eventFormatter.SetElement("BEST_ASK", 100.0);
							}
							else if (2 == tickCount)
							{
								eventFormatter.SetElement("BEST_BID", 99.0);
							}
							eventFormatter.SetElement("HIGH", 100 + tickCount * 0.01);
							eventFormatter.SetElement("LOW", 100 - tickCount * 0.005);
							++tickCount;
						}
					}
				}

				foreach (Message msg in eventObj)
				{
					Console.WriteLine(msg);
				}

				session.Publish(eventObj);
				Thread.Sleep(10 * 1000);
				if (tickCount % 3 == 0)
				{
					Deactivate(session);
					Thread.Sleep(10 * 1000);
					Activate(session);
				}
			}

			session.Stop();
		}

		public static void Main(String[] args)
		{
			Console.WriteLine("MktdataPublisherExample");
			MktdataPublisherExample example = new MktdataPublisherExample();
			example.Run(args);
			Console.WriteLine("Press ENTER to quit");
			Console.Read();
		}
	}
}
