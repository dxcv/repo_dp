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
using System.Collections;
using System.Threading;
using Bloomberglp.Blpapi;


namespace Bloomberglp.Blpapi.Examples
{
	class ContributionsPageExample
	{
		private const String AUTH_USER = "AuthenticationType=OS_LOGON";
		private const String AUTH_APP_PREFIX = "AuthenticationMode=APPLICATION_ONLY;ApplicationAuthenticationType=APPNAME_AND_KEY;ApplicationName=";
		private const String AUTH_DIR_PREFIX = "AuthenticationType=DIRECTORY_SERVICE;DirSvcPropertyName=";
		private const String AUTH_OPTION_NONE = "none";
		private const String AUTH_OPTION_USER = "user";
		private const String AUTH_OPTION_APP = "app=";
		private const String AUTH_OPTION_DIR = "dir=";

		private static readonly Name AUTHORIZATION_SUCCESS = Name.GetName("AuthorizationSuccess");
		private static readonly Name TOKEN_SUCCESS = Name.GetName("TokenGenerationSuccess");
		private static readonly Name SESSION_TERMINATED = Name.GetName("SessionTerminated");

		private List<string> d_serverHosts;
		private int d_serverPort;
		private String d_serviceName;
		private String d_topic;
		private String d_authOptions;
		private int d_maxEvents = 100;
		private int d_contributionId;
		private volatile bool d_running = true;

		enum AuthorizationStatus
		{
			WAITING,
			AUTHORIZED,
			FAILED
		};
		private Dictionary<CorrelationID, AuthorizationStatus> d_authorizationStatus =
					new Dictionary<CorrelationID, AuthorizationStatus>();

		public ContributionsPageExample()
		{
			d_serviceName = "//blp/mpfbapi";
			d_serverPort = 8194;
			d_serverHosts = new List<string>();
			d_authOptions = AUTH_USER;
			d_topic = "220/660/1";
			d_contributionId = 8563;
		}

		public void Run(String[] args)
		{
			if (!ParseCommandLine(args))
			{
				return;
			}

			SessionOptions.ServerAddress[] servers = new SessionOptions.ServerAddress[d_serverHosts.Count];
			for (int i = 0; i < d_serverHosts.Count; ++i)
			{
				servers[i] = new SessionOptions.ServerAddress(d_serverHosts[i], d_serverPort);
			}

			SessionOptions sessionOptions = new SessionOptions();
			sessionOptions.ServerAddresses = servers;
			sessionOptions.AuthenticationOptions = d_authOptions;
			sessionOptions.AutoRestartOnDisconnection = true;
			sessionOptions.NumStartAttempts = d_serverHosts.Count;

			System.Console.Write("Connecting to");
			foreach (SessionOptions.ServerAddress server in sessionOptions.ServerAddresses)
			{
				System.Console.Write(" " + server);
			}
			System.Console.WriteLine();
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

			TopicList topicList = new TopicList();
			topicList.Add(
				d_serviceName + "/" + d_topic,
				new CorrelationID(new MyStream(d_topic)));

			session.CreateTopics(
				topicList,
				ResolveMode.AUTO_REGISTER_SERVICES,
				identity);

			List<MyStream> myStreams = new List<MyStream>();
			for (int i = 0; i < topicList.Size; ++i)
			{
				if (topicList.StatusAt(i) == TopicList.TopicStatus.CREATED)
				{
					Topic topic = session.GetTopic(topicList.MessageAt(i));
					MyStream stream = (MyStream)topicList.CorrelationIdAt(i).Object;
					stream.SetTopic(topic);
					myStreams.Add(stream);
				}
			}

			PublishEvents(session, myStreams);

			session.Stop();
		}

		public static void Main(String[] args)
		{
			ContributionsPageExample example = new ContributionsPageExample();
			example.Run(args);
		}

		private void ProcessEvent(Event eventObj, ProviderSession session)
		{
			if (eventObj == null)
			{
				Console.WriteLine("Received null event ");
				return;
			}
			Console.WriteLine("Received event " + eventObj.Type.ToString());
			foreach (Message msg in eventObj)
			{
				Console.WriteLine("Message = " + msg);
				if (eventObj.Type == Event.EventType.SESSION_STATUS)
				{
					if (msg.MessageType == SESSION_TERMINATED)
					{
						d_running = false;
					}
					continue;
				}
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

			//TO DO Process event if needed.
		}

		#region private helper method

		private void PublishEvents(ProviderSession session, List<MyStream> myStreams)
		{
			Service service = session.GetService(d_serviceName);
			if (service == null)
			{
				System.Console.Error.WriteLine("Failed to get Service: " + d_serviceName);
				return;
			}
			Random rnd = new Random(DateTime.Now.Millisecond);

			int iteration = 0;
			while (iteration++ < d_maxEvents)
			{
				if (!d_running)
				{
					return;
				}
				Event eventObj = service.CreatePublishEvent();
				EventFormatter eventFormatter = new EventFormatter(eventObj);

				foreach (MyStream stream in myStreams)
				{
					eventFormatter.AppendMessage("PageData", stream.GetTopic());
					eventFormatter.PushElement("rowUpdate");

					eventFormatter.AppendElement();
					eventFormatter.SetElement("rowNum", 1);
					eventFormatter.PushElement("spanUpdate");

					eventFormatter.AppendElement();
					eventFormatter.SetElement("startCol", 20);
					eventFormatter.SetElement("length", 4);
					eventFormatter.SetElement("text", "TEST");
					eventFormatter.SetElement("attr", "INTENSIFY");
					eventFormatter.PopElement();

					eventFormatter.AppendElement();
					eventFormatter.SetElement("startCol", 25);
					eventFormatter.SetElement("length", 4);
					eventFormatter.SetElement("text", "PAGE");
					eventFormatter.SetElement("attr", "BLINK");
					eventFormatter.PopElement();

					eventFormatter.AppendElement();
					eventFormatter.SetElement("startCol", 30);
					String timestamp = System.DateTime.Now.ToString();
					eventFormatter.SetElement("length", timestamp.Length);
					eventFormatter.SetElement("text", timestamp);
					eventFormatter.SetElement("attr", "REVERSE");
					eventFormatter.PopElement();

					eventFormatter.PopElement();
					eventFormatter.PopElement();

					eventFormatter.AppendElement();
					eventFormatter.SetElement("rowNum", 2);
					eventFormatter.PushElement("spanUpdate");
					eventFormatter.AppendElement();
					eventFormatter.SetElement("startCol", 20);
					eventFormatter.SetElement("length", 9);
					eventFormatter.SetElement("text", "---------");
					eventFormatter.SetElement("attr", "UNDERLINE");
					eventFormatter.PopElement();
					eventFormatter.PopElement();
					eventFormatter.PopElement();

					eventFormatter.AppendElement();
					eventFormatter.SetElement("rowNum", 3);
					eventFormatter.PushElement("spanUpdate");
					eventFormatter.AppendElement();
					eventFormatter.SetElement("startCol", 10);
					eventFormatter.SetElement("length", 9);
					eventFormatter.SetElement("text", "TEST LINE");
					eventFormatter.PopElement();
					eventFormatter.AppendElement();
					eventFormatter.SetElement("startCol", 23);
					eventFormatter.SetElement("length", 5);
					eventFormatter.SetElement("text", "THREE");
					eventFormatter.PopElement();
					eventFormatter.PopElement();
					eventFormatter.PopElement();
					eventFormatter.PopElement();

					eventFormatter.SetElement("contributorId", d_contributionId);
					eventFormatter.SetElement("productCode", 1);
					eventFormatter.SetElement("pageNumber", 1);
				}

				foreach (Message msg in eventObj)
				{
					Console.WriteLine(msg.ToString());
				}

				session.Publish(eventObj);

				int sleepSecs = rnd.Next(20);
				Thread.Sleep(sleepSecs * 1000);
			}

		}

		private class MyStream
		{
			private String d_id;
			private Topic d_topic;

			public Topic GetTopic()
			{
				return d_topic;
			}

			public void SetTopic(Topic topic)
			{
				d_topic = topic;
			}

			public String SetId()
			{
				return d_id;
			}

			public MyStream(String id)
			{
				d_id = id;
				d_topic = null;
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

		private void PrintUsage()
		{
			Console.WriteLine("Usage:");
			Console.WriteLine("  Contribute market data to a topic");
			Console.WriteLine("     [-ip        <ipAddress = localhost>");
			Console.WriteLine("     [-p         <tcpPort   = 8194>");
			Console.WriteLine("     [-s         <service   = //blp/mpfbapi>]");
			Console.WriteLine("     [-t         <topic     = 220/660/1>]");
			Console.WriteLine("     [-me        <maxEvents = 100>]");
			Console.WriteLine("     [-c         <contributorId = 8563>]");
			Console.WriteLine("     [-auth      <option    = user> (user|none|app={app}|dir={property})]");

			Console.WriteLine("Press ENTER to quit");
		}

		private bool ParseCommandLine(String[] args)
		{
			for (int i = 0; i < args.Length; ++i)
			{
				if (string.Compare("-s", args[i], true) == 0
					&& i + 1 < args.Length)
				{
					d_serviceName = args[++i];
				}
				else if (string.Compare("-ip", args[i], true) == 0
					&& i + 1 < args.Length)
				{
					d_serverHosts.Add(args[++i]);
				}
				else if (string.Compare("-p", args[i], true) == 0
					&& i + 1 < args.Length)
				{
					d_serverPort = int.Parse(args[++i]);
				}
				else if (string.Compare("-t", args[i], true) == 0
					&& i + 1 < args.Length)
				{
					d_topic = args[++i];
				}
				else if (string.Compare("-me", args[i], true) == 0
					&& i + 1 < args.Length)
				{
					d_maxEvents = int.Parse(args[++i]);
				}
				else if (string.Compare("-c", args[i], true) == 0
					&& i + 1 < args.Length)
				{
					d_contributionId = int.Parse(args[++i]);
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
				else
				{
					PrintUsage();
					return false;
				}
			}
			if (d_serverHosts.Count == 0)
			{
				d_serverHosts.Add("localhost");
			}

			return true;
		}

		#endregion

	}

}
