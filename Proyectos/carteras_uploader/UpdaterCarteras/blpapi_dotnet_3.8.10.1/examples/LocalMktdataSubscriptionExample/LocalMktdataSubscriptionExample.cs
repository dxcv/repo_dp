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
using System.IO;
using System.Threading;

namespace Bloomberglp.Blpapi.Examples
{
	public class MktdataSubscriptionExample
	{
		private const String AUTH_USER = "AuthenticationType=OS_LOGON";
		private const String AUTH_APP_PREFIX = "AuthenticationMode=APPLICATION_ONLY;ApplicationAuthenticationType=APPNAME_AND_KEY;ApplicationName=";
		private const String AUTH_DIR_PREFIX = "AuthenticationType=DIRECTORY_SERVICE;DirSvcPropertyName=";
		private const String AUTH_OPTION_NONE = "none";
		private const String AUTH_OPTION_USER = "user";
		private const String AUTH_OPTION_APP = "app=";
		private const String AUTH_OPTION_DIR = "dir=";

		private Name AUTHORIZATION_SUCCESS = Name.GetName("AuthorizationSuccess");
		private Name TOKEN_SUCCESS = Name.GetName("TokenGenerationSuccess");

		private const String d_defaultHost      = "localhost";
		private const int    d_defaultPort      = 8194;
		private const String d_defaultService   = "//viper/mktdata";
		private const int    d_defaultMaxEvents = int.MaxValue;

		private List<String> d_hosts       = new List<String>();
		private int          d_port        = d_defaultPort;
		private String       d_service     = d_defaultService;
		private int          d_maxEvents   = d_defaultMaxEvents;
		private String       d_authOptions = AUTH_USER;
		private List<String> d_topics      = new List<String>();
		private List<String> d_fields      = new List<String>();
		private List<String> d_options     = new List<String>();

		public MktdataSubscriptionExample()
		{
		}

		public void Run(String[] args)
		{
			if (!ParseCommandLine(args))
				return;

			SessionOptions sessionOptions = new SessionOptions();
			SessionOptions.ServerAddress[] servers = new SessionOptions.ServerAddress[d_hosts.Count];
			for (int i = 0; i < d_hosts.Count; ++i)
			{
				servers[i] = new SessionOptions.ServerAddress(d_hosts[i], d_port);
			}
			sessionOptions.ServerAddresses = servers;
			sessionOptions.AutoRestartOnDisconnection = true;
			sessionOptions.NumStartAttempts = d_hosts.Count;
			sessionOptions.DefaultSubscriptionService = d_service;
			sessionOptions.AuthenticationOptions = d_authOptions;

			System.Console.WriteLine("Connecting to port " + d_port + " on ");
			foreach (string host in d_hosts)
			{
				System.Console.WriteLine(host + " ");
			}
			Session session = new Session(sessionOptions);

			if (!session.Start())
			{
				System.Console.Error.WriteLine("Failed to start session.");
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

			List<Subscription> subscriptions = new List<Subscription>();
			foreach (String topic in d_topics)
			{
				subscriptions.Add(new Subscription(
					d_service + topic,
					d_fields,
					d_options,
					new CorrelationID(topic)));
			}
			session.Subscribe(subscriptions, identity);
			ProcessSubscriptionResponse(session);
		}

		private bool Authorize(
				Service authService,
				Identity identity,
				Session session,
				CorrelationID cid)
		{
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

			session.SendAuthorizationRequest(authRequest, identity, cid);

			long startTime = System.DateTime.Now.Ticks;
			const int WAIT_TIME = 10 * 1000; // 10 seconds

			while (true)
			{
				eventObj = session.NextEvent(WAIT_TIME);
				if (eventObj.Type == Event.EventType.RESPONSE
					|| eventObj.Type == Event.EventType.PARTIAL_RESPONSE
					|| eventObj.Type == Event.EventType.REQUEST_STATUS)
				{
					foreach (Message msg in eventObj)
					{
						System.Console.WriteLine(msg.ToString());
						if (msg.MessageType == AUTHORIZATION_SUCCESS)
						{
							return true;
						}
						else
						{
							return false;
						}
					}
				}
				if (System.DateTime.Now.Ticks - startTime > WAIT_TIME * 10000)
				{
					return false;
				}
			}
		}
	
		private void PrintUsage()
		{
			Console.WriteLine("Usage:");
			Console.WriteLine(" [-ip    <ipAddress>] \tserver name or IP      (default = " + d_defaultHost + ")");
			Console.WriteLine(" [-p     <tcpPort>]   \tserver port            (default = " + d_defaultPort + ")");
			Console.WriteLine(" [-s     <service>]   \tservice name           (default = " + d_defaultService + ")");
			Console.WriteLine(" [-t     <topic>]     \ttopic to subscribed to (default = \"/ticker/IBM Equity\")");
			Console.WriteLine(" [-f    <field>]      \tfield to subscribe to  (default: empty)");
			Console.WriteLine(" [-o    <option>]     \tsubscription options   (default: empty)");
			Console.WriteLine(" [-me   <maxEvents>]  \tmax number of events   (default = " + d_defaultMaxEvents + ")");
			Console.WriteLine(" [-auth <option>]     \tauthorization option   (user|none|app={app}|dir={property})	(default = " + AUTH_OPTION_USER +")");
		}

		private bool ParseCommandLine(String[] args)
		{
			try
			{
				for (int i = 0; i < args.Length; ++i)
				{
					if (string.Compare("-s", args[i], true) == 0 && i + 1 < args.Length)
					{
						d_service = args[++i];
					}
					else if (string.Compare("-ip", args[i], true) == 0 && i + 1 < args.Length)
					{
						d_hosts.Add(args[++i]);
					}
					else if (string.Compare("-p", args[i], true) == 0 && i + 1 < args.Length)
					{
						d_port = int.Parse(args[++i]);
					}
					else if (string.Compare("-me", args[i], true) == 0 && i + 1 < args.Length)
					{
						d_maxEvents = int.Parse(args[++i]);
					}
					else if (string.Compare("-t", args[i], true) == 0 && i + 1 < args.Length)
					{
						d_topics.Add(args[++i]);
					}
					else if (string.Compare("-f", args[i], true) == 0 && i + 1 < args.Length)
					{
						d_fields.Add(args[++i]);
					}
					else if (string.Compare("-o", args[i], true) == 0 && i + 1 < args.Length)
					{
						d_options.Add(args[++i]);
					}
					else if (string.Compare("-auth", args[i], true) == 0 && i + 1 < args.Length)
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
					else
					{
						PrintUsage();
						return false;
					}
				}
			}
			catch (Exception)
			{
				PrintUsage();
				return false;
			}

			if (d_hosts.Count == 0)
			{
				d_hosts.Add("localhost");
			}
			if (d_topics.Count == 0)
			{
				d_topics.Add("/ticker/IBM Equity");
			}

			return true;
		}

		private void ProcessSubscriptionResponse(Session session)
		{
			int eventCount = 0;
			while (true)
			{
				Event eventObj = session.NextEvent();
				foreach (Message msg in eventObj)
				{
					if (eventObj.Type == Event.EventType.SUBSCRIPTION_DATA ||
						eventObj.Type == Event.EventType.SUBSCRIPTION_STATUS)
					{
						string topic = (string)msg.CorrelationID.Object;
						System.Console.WriteLine(topic + ": " + msg.AsElement);
					}
					else
					{
						System.Console.WriteLine(msg.AsElement);
					}
				}

				if (eventObj.Type == Event.EventType.SUBSCRIPTION_DATA)
				{
					if (++eventCount >= d_maxEvents)
					{
						break;
					}
				}
			}
		}

		public static void Main(String[] args)
		{
			MktdataSubscriptionExample example = new MktdataSubscriptionExample();
			try
			{
				example.Run(args);
			}
			catch (Exception e)
			{
				Console.WriteLine(e.ToString());
			}
		}
	}

}
