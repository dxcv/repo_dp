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

namespace Bloomberglp.Blpapi.Examples
{
	public class PageSubscriptionExample
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

		private int serverPort = 8194;
		private List<string> serverHosts = new List<string>();
		private string serviceName = "//viper/page";
		private string pageName = "330/1/1";
		private string authOptions = AUTH_USER;

		public void Run(String[] args)
		{
			Session session = null;
			if (!ParseCommandLine(args)) return;
			try
			{
				session = CreateSession();

				if (!session.Start())
				{
					System.Console.Error.WriteLine("Failed to start session.");
					return;
				}

				Identity identity = null;
				if (authOptions != null)
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

				if (!session.OpenService(serviceName))
				{
					System.Console.Error.WriteLine("Failed to open service :" + serviceName);
					return;
				}

				// Send subscription and handle subscription Reponse 
				SendProcessPageSubscription(session, identity);
			}
			catch (Exception ex)
			{
				Console.WriteLine("Failed to send Subscription due to error :" + ex.Message);
			}
			finally
			{
				session.Stop();
			}

		}

		public static void Main(String[] args)
		{
			System.Console.WriteLine("PageSubscriptionExample");
			PageSubscriptionExample example = new PageSubscriptionExample();
			example.Run(args);
			Console.WriteLine("Press ENTER to quit");
			System.Console.ReadLine();
		}

		#region private helper Method

		private Session CreateSession()
		{
			SessionOptions sessionOptions = new SessionOptions();
			SessionOptions.ServerAddress[] servers = new SessionOptions.ServerAddress[serverHosts.Count];
			for (int i = 0; i < serverHosts.Count; ++i)
			{
				servers[i] = new SessionOptions.ServerAddress(serverHosts[i], serverPort);
			}
			sessionOptions.ServerAddresses = servers;
			sessionOptions.AutoRestartOnDisconnection = true;
			sessionOptions.NumStartAttempts = serverHosts.Count;
			sessionOptions.AuthenticationOptions = authOptions;

			System.Console.WriteLine("Connecting to port " + serverPort + " on ");
			foreach (string host in serverHosts)
			{
				System.Console.WriteLine(host + " ");
			}
			Session session = new Session(sessionOptions);
			return session;
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

		private void SendProcessPageSubscription(Session session, Identity identity)
		{
			String topicName = serviceName + "/" + pageName;

			List<Subscription> subscriptionList = new List<Subscription>();
			subscriptionList.Add(new Subscription(topicName, new CorrelationID(topicName)));

			System.Console.WriteLine("Subscribing...");
			session.Subscribe(subscriptionList, identity);

			ProcessSubscriptionResponse(session);
		}

		private static void ProcessSubscriptionResponse(Session session)
		{
			while (true)
			{
				Event eventObj = session.NextEvent();
				System.Console.WriteLine("Got Event " + eventObj.Type.ToString());

				if (eventObj.Type == Event.EventType.SUBSCRIPTION_DATA || eventObj.Type == Event.EventType.SUBSCRIPTION_STATUS)
				{
					foreach (Message msg in eventObj)
					{
						if (msg != null)
						{

							String topic = (String)msg.CorrelationID.ToString();
							System.Console.WriteLine(topic + " - ");
							msg.Print(System.Console.Out);
						}
					}
				}
			}
		}

		private void PrintUsage()
		{
			Console.WriteLine("Usage:");
			Console.WriteLine(" Local Page Subscription ");
			Console.WriteLine("    [-ip   <ipAddress = localhost>]");
			Console.WriteLine("    [-p    <tcpPort   = " + serverPort + ">]");
			Console.WriteLine("    [-s    <service   = " + serviceName + ">]");
			Console.WriteLine("    [-P    <Page      = " + pageName + ">]");
			Console.WriteLine("    [-auth <user|none|app={app}|dir={property}> (default: user)]");
		}

		private bool ParseCommandLine(String[] args)
		{
			try
			{
				for (int i = 0; i < args.Length; ++i)
				{
					if (string.Compare("-s", args[i], true) == 0)
					{
						serviceName = args[++i];
					}
					else if (string.Compare("-ip", args[i], true) == 0)
					{
						serverHosts.Add(args[++i]);
					}
					else if (string.Compare("-p", args[i], true) == 0)
					{
						serverPort = int.Parse(args[++i]);
					}
					else if (string.Compare("-page", args[i], true) == 0)
					{
						pageName = args[++i];
					}
					else if (string.Compare("-auth", args[i], true) == 0
						&& i + 1 < args.Length)
					{
						++i;
						if (string.Compare(AUTH_OPTION_NONE, args[i], true) == 0)
						{
							authOptions = null;
						}
						else if (string.Compare(AUTH_OPTION_USER, args[i], true)
																		== 0)
						{
							authOptions = AUTH_USER;
						}
						else if (string.Compare(AUTH_OPTION_APP, 0, args[i], 0,
											AUTH_OPTION_APP.Length, true) == 0)
						{
							authOptions = AUTH_APP_PREFIX
								+ args[i].Substring(AUTH_OPTION_APP.Length);
						}
						else if (string.Compare(AUTH_OPTION_DIR, 0, args[i], 0,
											AUTH_OPTION_DIR.Length, true) == 0)
						{
							authOptions = AUTH_DIR_PREFIX
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
			}
			catch (Exception)
			{
				PrintUsage();
				return false;
			}
			if (serverHosts.Count == 0)
			{
				serverHosts.Add("localhost");
			}

			return true;
		}

		#endregion
	}
}
