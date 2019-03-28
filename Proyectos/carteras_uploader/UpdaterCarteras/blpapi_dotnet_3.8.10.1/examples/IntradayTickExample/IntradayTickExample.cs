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
using DateTime = System.DateTime;
using DayOfWeek = System.DayOfWeek;
using Datetime = Bloomberglp.Blpapi.Datetime;
using Event = Bloomberglp.Blpapi.Event;
using Element = Bloomberglp.Blpapi.Element;
using Message = Bloomberglp.Blpapi.Message;
using Name = Bloomberglp.Blpapi.Name;
using Request = Bloomberglp.Blpapi.Request;
using Service = Bloomberglp.Blpapi.Service;
using Session = Bloomberglp.Blpapi.Session;

using ArrayList = System.Collections.ArrayList;

namespace Bloomberglp.Blpapi.Examples
{
	public class IntradayTickExample
	{
		private static readonly Name TICK_DATA      = new Name("tickData");
		private static readonly Name COND_CODE	    = new Name("conditionCodes");
		private static readonly Name SIZE		    = new Name("size");
		private static readonly Name TIME		    = new Name("time");
		private static readonly Name TYPE		    = new Name("type");
		private static readonly Name VALUE		    = new Name("value");
		private static readonly Name RESPONSE_ERROR = new Name("responseError");
		private static readonly Name CATEGORY       = new Name("category");
		private static readonly Name MESSAGE        = new Name("message");

		private string            d_host;
		private int               d_port;
		private string            d_security;
		private ArrayList         d_events;
		private bool              d_conditionCodes;
		private string            d_startDateTime;
		private string            d_endDateTime;		

		public static void Main(string[] args)
		{
			System.Console.WriteLine("Intraday Rawticks Example");
			IntradayTickExample example = new IntradayTickExample();
			example.run(args);

			System.Console.WriteLine("Press ENTER to quit");
			System.Console.Read();
		}

		private string getPreviousTradingDate()
		{
			DateTime tradedOn = DateTime.Now;
			tradedOn = tradedOn.AddDays(-1);
			if (tradedOn.DayOfWeek == DayOfWeek.Sunday)
			{
				tradedOn = tradedOn.AddDays(-2);
			}
			else if (tradedOn.DayOfWeek == DayOfWeek.Saturday)
			{
				tradedOn = tradedOn.AddDays(-1);
			}
			string prevDate = tradedOn.Year.ToString() + "-" +
							  tradedOn.Month.ToString() + "-" +
							  tradedOn.Day.ToString();
			return prevDate;
		}

        public IntradayTickExample()
		{
			d_host = "localhost";
			d_port = 8194;
			d_security = "IBM US Equity";
			d_events = new ArrayList();
			d_conditionCodes = false;

			string prevTradingDate = getPreviousTradingDate();
			d_startDateTime = prevTradingDate + "T15:30:00";
			d_endDateTime = prevTradingDate + "T15:35:00";
		}

		private void run(string[] args)
		{
			if (!parseCommandLine(args)) return;

			SessionOptions sessionOptions = new SessionOptions();
			sessionOptions.ServerHost = d_host;
			sessionOptions.ServerPort = d_port;

			System.Console.WriteLine("Connecting to " + d_host + ":" + d_port);
			Session session = new Session(sessionOptions);
			bool sessionStarted = session.Start();
			if (!sessionStarted)
			{
				System.Console.Error.WriteLine("Failed to start session.");
				return;
			}
			if (!session.OpenService("//blp/refdata"))
			{
				System.Console.Error.WriteLine("Failed to open //blp/refdata");
				return;
			}

			sendIntradayTickRequest(session);

			// wait for events from session.
			eventLoop(session);

			session.Stop();
		}

		private void eventLoop(Session session)
		{
			bool done = false;
			while (!done) 
			{
				Event eventObj = session.NextEvent();
				if (eventObj.Type == Event.EventType.PARTIAL_RESPONSE) 
				{
					System.Console.WriteLine("Processing Partial Response");
					processResponseEvent(eventObj);
				}
				else if (eventObj.Type == Event.EventType.RESPONSE) 
				{
					System.Console.WriteLine("Processing Response");
					processResponseEvent(eventObj);
					done = true;
				} 
				else
				{
					foreach (Message msg in eventObj)
					{
						System.Console.WriteLine(msg.AsElement);
						if (eventObj.Type == Event.EventType.SESSION_STATUS) 
						{
							if (msg.MessageType.Equals("SessionTerminated")) 
							{
								done = true;
							}
						}
					}
				}
			}
		}

		private void processMessage(Message msg)
		{
			Element data = msg.GetElement(TICK_DATA).GetElement(TICK_DATA); ;
			int numItems = data.NumValues;
			System.Console.WriteLine("TIME\t\t\tTYPE\tVALUE\t\tSIZE\tCC");
			System.Console.WriteLine("----\t\t\t----\t-----\t\t----\t--");
			for (int i = 0; i < numItems; ++i)
			{
				Element item = data.GetValueAsElement(i);
				Datetime time = item.GetElementAsDate(TIME);
				string type = item.GetElementAsString(TYPE);
				double value = item.GetElementAsFloat64(VALUE);
				int size = item.GetElementAsInt32(SIZE);
				string cc = "";
				if (item.HasElement(COND_CODE))
				{
					cc = item.GetElementAsString(COND_CODE);
				}

				System.DateTime sysDatetime =
					new System.DateTime(time.Year, time.Month, time.DayOfMonth,
							time.Hour, time.Minute, time.Second, time.MilliSecond);
				System.Console.WriteLine(
					sysDatetime.ToString("s") + "\t" +
					type + "\t" +
					value.ToString("C") + "\t\t" +
					size + "\t" +
					cc);
			}
		}

		
		private void processResponseEvent(Event eventObj)
		{
			foreach (Message msg in eventObj)
			{
				if (msg.HasElement(RESPONSE_ERROR))
				{
					printErrorInfo("REQUEST FAILED: ", msg.GetElement(RESPONSE_ERROR));
					continue;
				}
				processMessage(msg);
			}
		}

		private void sendIntradayTickRequest(Session session)
		{
			Service refDataService = session.GetService("//blp/refdata");
			Request request = refDataService.CreateRequest("IntradayTickRequest");

			request.Set("security", d_security);

			// Add fields to request
			Element eventTypes = request.GetElement("eventTypes");
			for (int i = 0; i < d_events.Count; ++i)
			{
				eventTypes.AppendValue((string)d_events[i]);
			}

			// All times are in GMT
			request.Set("startDateTime", d_startDateTime);
			request.Set("endDateTime", d_endDateTime);

			if (d_conditionCodes) 
			{
				request.Set("includeConditionCodes", true);
			}

			System.Console.WriteLine("Sending Request: " + request);
			session.SendRequest(request, null);
		}

		private bool parseCommandLine(string[] args)
		{
			for (int i = 0; i < args.Length; ++i) 
			{
				if (string.Compare(args[i], "-s", true) == 0)
				{
					d_security = args[i+1];
				}
				else if (string.Compare(args[i], "-e", true) == 0)
				{
					d_events.Add(args[i+1]);
				}
				else if (string.Compare(args[i], "-cc", true) == 0)				
				{
					d_conditionCodes = true;
				}
				else if (string.Compare(args[i], "-sd", true) == 0)
				{
					d_startDateTime = args[i+1];
				}
				else if (string.Compare(args[i], "-ed", true) == 0)
				{
					d_endDateTime = args[i+1];
				}
				else if (string.Compare(args[i], "-ip", true) == 0)
				{
					d_host = args[i+1];
				}
				else if (string.Compare(args[i], "-p", true) == 0)				
				{
					d_port = int.Parse(args[i+1]);
				}
				else if (string.Compare(args[i], "-h", true) == 0)				
				{
					printUsage();
					return false;
				}
			}

			if (d_events.Count == 0) 
			{
				d_events.Add("TRADE");
			}

			return true;
		}

		private void printErrorInfo(string leadingStr, Element errorInfo)
		{
			System.Console.WriteLine(leadingStr + errorInfo.GetElementAsString(CATEGORY) +
				" (" + errorInfo.GetElementAsString(MESSAGE) + ")");
		}

		private void printUsage()
		{
			System.Console.WriteLine("Usage:");
			System.Console.WriteLine("	Retrieve intraday rawticks ");
			System.Console.WriteLine("		[-s		<security	= IBM US Equity>");
			System.Console.WriteLine("		[-e		<event		= TRADE>");
			System.Console.WriteLine("        [-sd    <startDateTime  = 2007-03-26T09:30:00>");
			System.Console.WriteLine("        [-ed    <endDateTime    = 2007-03-26T10:30:00>");
			System.Console.WriteLine("		[-cc	<includeConditionCodes = false>");
			System.Console.WriteLine("		[-ip 	<ipAddress	= localhost>");
			System.Console.WriteLine("		[-p 	<tcpPort	= 8194>");
			System.Console.WriteLine("Notes:");
			System.Console.WriteLine("1) All times are in GMT.");
			System.Console.WriteLine("2) Only one security can be specified.");
		}
	}
}
