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


namespace Bloomberglp.Blpapi.Examples
{
	public class ServiceSchemaDumpExample
	{

		private String serviceName;
		private int serverPort;
		private String serverHost;
		
		public ServiceSchemaDumpExample()
		{
			serviceName = "//blp/mktdata";
			serverPort = 8194;
			serverHost = "localhost";
		}

		public void run(String[] args)
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

				if (!session.OpenService(serviceName))
				{
					System.Console.Error.WriteLine("Failed to open service :" + serviceName);
					return;
				}

				Service service = session.GetService(serviceName);

				// Dump schema for the service
				Console.WriteLine("Schema for service:" + serviceName + "\n\n");
				for (int i = 0; i < service.NumEventDefinitions; ++i)
				{
					SchemaElementDefinition eventDefinition = service.GetEventDefinition(i);
					Console.WriteLine(eventDefinition);
				}
				Console.WriteLine("");
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

		public static void Main(String[] args) //throws Exception 
		{
			try
			{

				ServiceSchemaDumpExample example = new ServiceSchemaDumpExample();
				example.run(args);
			}
			catch (Exception ex)
			{
				Console.WriteLine(ex.ToString());
			}
		}

		private void processEvent(Event eventobj, Session session)
		{
			Console.WriteLine("Received event " + eventobj.Type.ToString());

			foreach (Message msg in eventobj)
			{
				Console.WriteLine("Message = " + msg);
			}
		}

		private Session CreateSession()
		{
			SessionOptions sessionOptions = new SessionOptions();
			sessionOptions.ServerHost = serverHost;
			sessionOptions.ServerPort = serverPort;

			System.Console.WriteLine("Connecting to " + serverHost +
				":" + serverPort);
			Session session = new Session(sessionOptions);
			return session;
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
						serverHost = args[++i];
					}
					else if (string.Compare("-p", args[i], true) == 0)
					{
						serverPort = int.Parse(args[++i]);
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

			return true;
		}

		private void PrintUsage()
		{
			Console.WriteLine("Usage:");
			Console.WriteLine("	Publish on a topic ");
			Console.WriteLine("		[-ip 		<ipAddress	= localhost>");
			Console.WriteLine("		[-p 		<tcpPort	= 8194>");
			Console.WriteLine("		[-s         <service Name = //blp/mktdata>]");
		}

		
	}

}
