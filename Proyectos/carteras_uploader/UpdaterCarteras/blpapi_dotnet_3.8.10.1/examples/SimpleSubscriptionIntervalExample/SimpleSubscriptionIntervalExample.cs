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
using Event = Bloomberglp.Blpapi.Event;
using Message = Bloomberglp.Blpapi.Message;
using Name = Bloomberglp.Blpapi.Name;
using Session = Bloomberglp.Blpapi.Session;

namespace Bloomberglp.Blpapi.Examples
{

	public class SimpleSubscriptionIntervalExample
	{
		/**
		 * @param args
		 */
		public static void Main(string[] args)
		{
			SimpleSubscriptionIntervalExample example =
				new SimpleSubscriptionIntervalExample();
			example.run(args);
			System.Console.WriteLine("Press ENTER to quit");
			System.Console.Read();
		}

		private void run(string[] args)
		{
			string serverHost = "localhost";
			int serverPort = 8194;

			SessionOptions sessionOptions = new SessionOptions();
			sessionOptions.ServerHost = serverHost;
			sessionOptions.ServerPort = serverPort;

			System.Console.WriteLine("Connecting to " + serverHost + ":" + serverPort);
			Session session = new Session(sessionOptions);
			bool sessionStarted = session.Start();
			if (!sessionStarted)
			{
				System.Console.Error.WriteLine("Failed to start session.");
				return;
			}
			if (!session.OpenService("//blp/mktdata"))
			{
				System.Console.Error.WriteLine("Failed to open //blp/mktdata");
				return;
			}

			System.Collections.Generic.List<Subscription> subscriptions
			   = new System.Collections.Generic.List<Subscription>();

			// subscribe with a 1 second interval
			string security = "IBM US Equity";
			subscriptions.Add(new Subscription(
								security,
								"LAST_PRICE,BID,ASK",
								"interval=1.0",
								new CorrelationID(security))
							  );
			session.Subscribe(subscriptions);

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
			}
		}
	}
}
