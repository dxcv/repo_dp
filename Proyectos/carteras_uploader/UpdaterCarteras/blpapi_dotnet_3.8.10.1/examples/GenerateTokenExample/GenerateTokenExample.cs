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

using CorrelationID = Bloomberglp.Blpapi.CorrelationID;
using Event = Bloomberglp.Blpapi.Event;
using EventQueue = Bloomberglp.Blpapi.EventQueue;
using Element = Bloomberglp.Blpapi.Element;
using Message = Bloomberglp.Blpapi.Message;
using Name = Bloomberglp.Blpapi.Name;
using Request = Bloomberglp.Blpapi.Request;
using Service = Bloomberglp.Blpapi.Service;
using Session = Bloomberglp.Blpapi.Session;
using Identity = Bloomberglp.Blpapi.Identity;
using SessionOptions = Bloomberglp.Blpapi.SessionOptions;

namespace Bloomberglp.Blpapi.Examples
{
	public class GenerateTokenExample
	{
		private Name AUTHORIZATION_SUCCESS = Name.GetName("AuthorizationSuccess");
		private Name AUTHORIZATION_FAILURE = Name.GetName("AuthorizationFailure");
		private Name TOKEN_SUCCESS = Name.GetName("TokenGenerationSuccess");
		private Name TOKEN_FAILURE = Name.GetName("TokenGenerationFailure");

		private String serverHost;
		private int serverPort;
		private String DSProperty;
		bool useDS;
		private Session session;
		private Identity identity;
		private List<string> d_securities;
		private List<string> d_fields;

		string token;

		string authServiceName = "//blp/apiauth";

		Service authService = null;

		public GenerateTokenExample()
		{
			serverHost = "localhost";
			serverPort = 8194;
			DSProperty = "";
			useDS = false;
			session = null;
			d_securities = new List<string>();
			d_fields = new List<string>();
		}

		public void Run(String[] args)
		{
			if (!ParseCommandLine(args)) return;

			session = CreateSession();

			try
			{
				if (!session.Start())
				{
					System.Console.WriteLine("Failed to start session.");
					return;
				}

				// Authenticate user using Generate Token Request 
				if (!GenerateToken(out token)) return;

				//Authorization : pass Token into authorization request .Returns User handle with user's entitlements info set by server  .
				if (!IsBPipeAuthorized(token, out identity)) return;

				// send request using authorized user handle
				SendRequest(identity);

				// process response.
				bool isRunning = true;
				while (isRunning)
				{
					Event eventObj = session.NextEvent();
					foreach (Message msg in eventObj)
					{
						if (eventObj.Type == Event.EventType.RESPONSE)
						{
							System.Console.WriteLine(msg);
							isRunning = false;
						}
					}
				}
			}
			finally
			{
				session.Stop();
			}

		}

		public static void Main(String[] args)
		{
			System.Console.WriteLine("GenerateToken");
			GenerateTokenExample example = new GenerateTokenExample();
			example.Run(args);
			System.Console.WriteLine("Press ENTER to quit");
			System.Console.Read();
		}

		#region private Helper member

		private Session CreateSession()
		{
			SessionOptions sessionOptions = new SessionOptions();
			sessionOptions.ServerHost = serverHost;
			sessionOptions.ServerPort = serverPort;
			String authOptions = "AuthenticationType=OS_LOGON";

			if (useDS)
			{
				authOptions = "AuthenticationType=DIRECTORY_SERVICE;DirSvcPropertyName=";
				authOptions += DSProperty;
			}

			System.Console.WriteLine("Authentication Options = " + authOptions);
			sessionOptions.AuthenticationOptions = authOptions;
			System.Console.WriteLine("Connecting to " + serverHost + ":" + serverPort);	

			session = new Session(sessionOptions);
			return session;
		}

		private bool GenerateToken(out string token)
		{
			bool isTokenSuccess = false;
			bool isRunning = false;

			token = string.Empty;
			CorrelationID tokenReqId = new CorrelationID(99);
			EventQueue tokenEventQueue = new EventQueue();

			try
			{
				session.GenerateToken(tokenReqId, tokenEventQueue);
			}
			catch (Exception e)
			{
				System.Console.Error.WriteLine(e.Message);
				return false;
			}

			while (!isRunning)
			{
				Event eventObj = tokenEventQueue.NextEvent();
				if (eventObj.Type == Event.EventType.TOKEN_STATUS ||
					eventObj.Type == Event.EventType.REQUEST_STATUS)
				{
					System.Console.WriteLine("processTokenEvents");
					foreach (Message msg in eventObj)
					{
						System.Console.WriteLine(msg.ToString());
						if (msg.MessageType == TOKEN_SUCCESS)
						{
							token = msg.GetElementAsString("token");
							isTokenSuccess = true;
							isRunning = true;
							break;
						}
						else if (msg.MessageType == TOKEN_FAILURE)
						{
							Console.WriteLine("Received : " + TOKEN_FAILURE.ToString());
							isRunning = true;
							break;
						}
						else
						{
							Console.WriteLine("Error while Token Generation");
							isRunning = true;
							break;
						}
					}
				}
			}

			return isTokenSuccess;
		}

		private bool IsBPipeAuthorized(string token , out Identity identity)
		{
			bool isAuthorized = false;
			bool isRunning = true;
			identity = null;

			if (!session.OpenService(authServiceName))
			{
				System.Console.Error.WriteLine("Failed to open //blp/apiauth");
				return (isAuthorized = false);

			}
			authService = session.GetService(authServiceName);


			Request authRequest = authService.CreateAuthorizationRequest();

			authRequest.Set("token", token);
			identity = session.CreateIdentity();
			EventQueue authEventQueue = new EventQueue();

			session.SendAuthorizationRequest(authRequest, identity, authEventQueue, new CorrelationID(1));

			while (isRunning)
			{
				Event eventObj = authEventQueue.NextEvent();
				System.Console.WriteLine("processEvent");
				if (eventObj.Type == Event.EventType.RESPONSE ||
					eventObj.Type == Event.EventType.PARTIAL_RESPONSE ||
					eventObj.Type == Event.EventType.REQUEST_STATUS)
				{
					foreach (Message msg in eventObj)
					{
						if (msg.MessageType == AUTHORIZATION_SUCCESS)
						{
							System.Console.WriteLine("Authorization SUCCESS");

							isAuthorized = true;
							isRunning = false;
							break;
						}
						else if (msg.MessageType == AUTHORIZATION_FAILURE)
						{
							System.Console.WriteLine("Authorization FAILED");
							System.Console.WriteLine(msg);
							isRunning = false;
						}
						else
						{
							System.Console.WriteLine(msg);
						}
					}
				}
			}

			return isAuthorized;
		}

		private void SendRequest(Identity identity)
		{
			if (!session.OpenService("//blp/refdata"))
			{
				System.Console.Error.WriteLine("Failed to open //blp/refdata");
				return;
			}

			Service refDataService = session.GetService("//blp/refdata");
			Request request = refDataService.CreateRequest("ReferenceDataRequest");

			// append securities to request
			foreach (String security in d_securities)
			{
				request.Append("securities", security);
			}

			// append fields to request
			foreach (String field in d_fields)
			{
				request.Append("fields", field);
			}

			System.Console.WriteLine("Sending Request: " + request);

			session.SendRequest(request, identity, new CorrelationID(2));
		}

		private void PrintUsage()
		{
			System.Console.WriteLine("Usage:");
			System.Console.WriteLine("	Generate a token for authorization ");
			System.Console.WriteLine("		[-ip 		<ipAddress	= localhost>");
			System.Console.WriteLine("		[-p 		<tcpPort	= 8194>");
			System.Console.WriteLine("		[-s 		<security	= IBM US Equity>");
			System.Console.WriteLine("		[-f 		<field		= PX_LAST>");
			System.Console.WriteLine("		[-d			<dirSvcProperty = NULL>");
		}

		private bool ParseCommandLine(String[] args)
		{
			for (int i = 0; i < args.Length; ++i)
			{
				if (string.Compare("-ip", args[i], true) == 0)
				{
					serverHost = args[++i];
				}
				else if (string.Compare("-p", args[i], true) == 0)
				{
					serverPort = int.Parse(args[++i]);
				}
				else if (string.Compare("-s", args[i], true) == 0)
				{
					d_securities.Add(args[++i]);
				}
				else if (string.Compare("-f", args[i], true) == 0)
				{
					d_fields.Add(args[++i]);
				}
				else if (string.Compare("-d", args[i], true) == 0)
				{
					useDS = true;
					DSProperty = args[++i];
				}
				else
				{
					PrintUsage();
					return false;
				}
			}

			if (d_securities.Count == 0)
			{
				d_securities.Add("IBM US Equity");
			}

			if (d_fields.Count == 0)
			{
				d_fields.Add("PX_LAST");
			}

			return true;
		}

		#endregion
	}
}

