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
using System.Threading;

using Bloomberglp.Blpapi;

namespace Bloomberglp.Blpapi.Examples
{
	class PageBroadcastPublisherExample
	{
		private static readonly Name AUTHORIZATION_SUCCESS = Name.GetName("AuthorizationSuccess");
		private static readonly Name PERMISSION_REQUEST = Name.GetName("PermissionRequest");
		private static readonly Name TOPIC_SUBSCRIBED = Name.GetName("TopicSubscribed");
		private static readonly Name TOPIC_RECAP = Name.GetName("TopicRecap");
		private static readonly Name TOKEN_SUCCESS = Name.GetName("TokenGenerationSuccess");
		private static readonly Name SESSION_TERMINATED = Name.GetName("SessionTerminated");

		private const String AUTH_USER = "AuthenticationType=OS_LOGON";
		private const String AUTH_APP_PREFIX = "AuthenticationMode=APPLICATION_ONLY;ApplicationAuthenticationType=APPNAME_AND_KEY;ApplicationName=";
		private const String AUTH_DIR_PREFIX = "AuthenticationType=DIRECTORY_SERVICE;DirSvcPropertyName=";
		private const String AUTH_OPTION_NONE = "none";
		private const String AUTH_OPTION_USER = "user";
		private const String AUTH_OPTION_APP = "app=";
		private const String AUTH_OPTION_DIR = "dir=";

		private const string AUTH_SERVICE_NAME = "//blp/apiauth";

		private String d_service = "//viper/page";
		private int d_verbose = 0;
		private List<String> d_hosts = new List<String>();
		private int d_port = 8194;

		private String d_groupId = null;
		private int d_priority = int.MaxValue;
		private volatile bool d_running = true;

		private String d_authOptions = AUTH_USER;

		enum AuthorizationStatus
		{
			WAITING,
			AUTHORIZED,
			FAILED
		};
		private Dictionary<CorrelationID, AuthorizationStatus> d_authorizationStatus =
					new Dictionary<CorrelationID, AuthorizationStatus>();

		
		private class MyStream
		{
			String d_id;
			Topic d_topic;

			public MyStream()
			{
				d_id = "";
			}

			public MyStream(String id)
			{
				d_id = id;
			}

			public void setTopic(Topic topic)
			{
				d_topic = topic;
			}

			public String getId()
			{
				return d_id;
			}

			public Topic getTopic()
			{
				return d_topic;
			}
		};

		private void ProcessTopicStatusEvent(Event eventObj, ProviderSession session)
		{
			foreach (Message msg in eventObj)
			{
				Console.WriteLine(msg);
				if (msg.MessageType == TOPIC_RECAP || msg.MessageType == TOPIC_SUBSCRIBED)
				{
					Topic topic = session.GetTopic(msg);
					if (topic != null)
					{
						// send initial paint, this should come from my own cache
						Service service = session.GetService(d_service);
						if (service == null)
						{
							Console.Error.WriteLine("service unavailable");
							return;
						}
						Event recapEvent = service.CreatePublishEvent();
						EventFormatter eventFormatter = new EventFormatter(recapEvent);
						CorrelationID recapCid = msg.MessageType == TOPIC_RECAP ? 
							msg.CorrelationID	//solicited recap
							: null;				//unsolicited recap
						eventFormatter.AppendRecapMessage(
							topic, 
							recapCid);
						eventFormatter.SetElement("numRows", 25);
						eventFormatter.SetElement("numCols", 80);
						eventFormatter.PushElement("rowUpdate");
						for (int i = 1; i <= 5; ++i)
						{
							eventFormatter.AppendElement();
							eventFormatter.SetElement("rowNum", i);
							eventFormatter.PushElement("spanUpdate");
							eventFormatter.AppendElement();
							eventFormatter.SetElement("startCol", 1);
							eventFormatter.SetElement("length", 10);
							eventFormatter.SetElement("text", "RECAP");
							eventFormatter.PopElement();
							eventFormatter.PopElement();
							eventFormatter.PopElement();
						}
						eventFormatter.PopElement();
						session.Publish(recapEvent);
					}
				}
			}
		}

		private void ProcessRequestEvent(Event eventObj, ProviderSession session)
		{
			foreach (Message msg in eventObj)
			{
				Console.WriteLine(msg);
				if (msg.MessageType == PERMISSION_REQUEST)
				{
					Service pubService = session.GetService(d_service);
					if (pubService == null)
					{
						Console.Error.WriteLine("service unavailable");
						return;
					}
					Event response = pubService.CreateResponseEvent(msg.CorrelationID);
					EventFormatter ef = new EventFormatter(response);
					ef.AppendResponse("PermissionResponse");
					ef.PushElement("topicPermissions"); // TopicPermissions

					Element topicElement = msg.GetElement(Name.GetName("topics"));
					for (int i = 0; i < topicElement.NumValues; ++i)
					{
						ef.AppendElement();
						ef.SetElement("topic", topicElement.GetValueAsString(i));
						ef.SetElement("result", 0); // ALLOWED: 0, DENIED: 1
						ef.PopElement();
					}

					session.SendResponse(response);
				}
			}
		}

		private void ProcessResponseEvent(Event eventObj, ProviderSession session)
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

		private void ProcessEvent(Event eventObj, ProviderSession session)
		{
			switch (eventObj.Type)
			{
				case Event.EventType.TOPIC_STATUS:
					ProcessTopicStatusEvent(eventObj, session);
					break;
				case Event.EventType.REQUEST:
					ProcessRequestEvent(eventObj, session);
					break;
				case Event.EventType.RESPONSE:
				case Event.EventType.PARTIAL_RESPONSE:
				case Event.EventType.REQUEST_STATUS:
					ProcessResponseEvent(eventObj, session);
					break;
				case Event.EventType.SESSION_STATUS:
					foreach (Message msg in eventObj)
					{
						Console.WriteLine(msg);
						if (msg.MessageType == SESSION_TERMINATED)
						{
							d_running = false;
						}
					}
					break;
				default:
					PrintMessage(eventObj);
					break;
			}
		}

		private void PrintUsage()
		{
			Console.WriteLine("Broadcast page data.");
			Console.WriteLine("Usage:");
			Console.WriteLine("\t[-ip   <ipAddress>]  \tserver name or IP (default: localhost)");
			Console.WriteLine("\t[-p    <tcpPort>]    \tserver port (default: 8194)");
			Console.WriteLine("\t[-s    <service>]    \tservice name (default: //viper/page)");
			Console.WriteLine("\t[-g    <groupId>]    \tpublisher groupId (defaults to a unique value)");
			Console.WriteLine("\t[-pri  <priority>]   \tpublisher priority (default: Integer.MAX_VALUE)");
			Console.WriteLine("\t[-v]                 \tincrease verbosity (can be specified more than once)");
			Console.WriteLine("\t[-auth <option>]     \tauthentication option: user|none|app=<app>|userapp=<app>|dir=<property> (default: user)");
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
				else if (string.Compare("-auth", args[i], true) == 0
						&& i + 1 < args.Length)
				{
					++i;
					if (string.Compare(AUTH_OPTION_NONE, args[i], true) == 0)
					{
						d_authOptions = null;
					}
					else if (string.Compare(AUTH_OPTION_USER, args[i], true) == 0)
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

		private void PrintMessage(Event eventObj)
		{
			foreach (Message msg in eventObj)
			{
				Console.WriteLine(msg);
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

		private void Publish(TopicList topicList, ProviderSession session)
		{
			List<MyStream> myStreams = new List<MyStream>();
			for (int i = 0; i < topicList.Size; ++i)
			{
				if (topicList.StatusAt(i) == TopicList.TopicStatus.CREATED)
				{
					Message message = topicList.MessageAt(i);
					Topic topic = session.GetTopic(message);
					MyStream stream = (MyStream)topicList.CorrelationIdAt(i).Object;
					stream.setTopic(topic);
					myStreams.Add(stream);
					Console.WriteLine("Topic created: " + stream.getId());
				}
			}

			Service pubService = session.GetService(d_service);
			if (pubService == null)
			{
				Console.Error.WriteLine("service unavailable");
				return;
			}

			// Now we will start publishing
			Event eventObj = pubService.CreatePublishEvent();
			EventFormatter eventFormatter = new EventFormatter(eventObj);
			for (int index = 0; index < myStreams.Count; index++)
			{
				MyStream stream = (MyStream)myStreams[index];

				eventFormatter.AppendRecapMessage(stream.getTopic(), null);
				eventFormatter.SetElement("numRows", 25);
				eventFormatter.SetElement("numCols", 80);
				eventFormatter.PushElement("rowUpdate");
				for (int i = 1; i <= 5; ++i)
				{
					eventFormatter.AppendElement();
					eventFormatter.SetElement("rowNum", i);
					eventFormatter.PushElement("spanUpdate");
					eventFormatter.AppendElement();
					eventFormatter.SetElement("startCol", 1);
					eventFormatter.SetElement("length", 10);
					eventFormatter.SetElement("text", "INITIAL");
					eventFormatter.SetElement("fgColor", "RED");
					eventFormatter.PushElement("attr");
					eventFormatter.AppendValue("UNDERLINE");
					eventFormatter.AppendValue("BLINK");
					eventFormatter.PopElement();
					eventFormatter.PopElement();
					eventFormatter.PopElement();
					eventFormatter.PopElement();
				}
				eventFormatter.PopElement();
			}
			if (d_verbose > 0)
			{
				PrintMessage(eventObj);
			}
			session.Publish(eventObj);

			while (d_running)
			{
				eventObj = pubService.CreatePublishEvent();
				eventFormatter = new EventFormatter(eventObj);

				for (int index = 0; index < myStreams.Count; index++)
				{
					MyStream stream = (MyStream)myStreams[index];
					eventFormatter.AppendMessage("RowUpdate", stream.getTopic());
					eventFormatter.SetElement("rowNum", 1);
					eventFormatter.PushElement("spanUpdate");
					eventFormatter.AppendElement();
					eventFormatter.SetElement("startCol", 1);
					String text = System.DateTime.Now.ToString();
					eventFormatter.SetElement("length", text.Length);
					eventFormatter.SetElement("text", text);
					eventFormatter.PopElement();
					eventFormatter.AppendElement();
					eventFormatter.SetElement("startCol", text.Length + 10);
					text = System.DateTime.Now.ToString();
					eventFormatter.SetElement("length", text.Length);
					eventFormatter.SetElement("text", text);
					eventFormatter.PopElement();
					eventFormatter.PopElement();
				}

				if (d_verbose > 0)
				{
					PrintMessage(eventObj);
				}
				session.Publish(eventObj);
				Thread.Sleep(10 * 1000);
			}
		}

		public void Run(String[] args) //throws Exception
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
			sessionOptions.NumStartAttempts = servers.Length;

			Console.Write("Connecting to");
			foreach (SessionOptions.ServerAddress server in sessionOptions.ServerAddresses)
			{
				Console.Write(" " + server);
			}
			Console.WriteLine();

			ProviderSession session = new ProviderSession(
					sessionOptions,
					ProcessEvent);

			if (!session.Start())
			{
				Console.WriteLine("Failed to start session");
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

			TopicList topicList = new TopicList();
			topicList.Add(
				d_service + "/1245/4/5",
				new CorrelationID(new MyStream("1245/4/5")));
			topicList.Add(
				d_service + "/330/1/1",
				new CorrelationID(new MyStream("330/1/1")));

			session.CreateTopics(
				topicList,
				ResolveMode.AUTO_REGISTER_SERVICES,
				identity);
			// createTopics() is synchronous, topicList will be updated
			// with the results of topic creation (resolution will happen
			// under the covers)

			Publish(topicList, session);
		}

		public static void Main(String[] args)
		{
			Console.WriteLine("PageBroadcastPublisherExample");
			PageBroadcastPublisherExample example = new PageBroadcastPublisherExample();
			example.Run(args);

			Console.WriteLine("Press <ENTER> to terminate.");
			Console.ReadLine();
		}
	}
}
