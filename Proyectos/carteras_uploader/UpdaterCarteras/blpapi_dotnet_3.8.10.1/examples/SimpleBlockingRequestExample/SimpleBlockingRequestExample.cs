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

using Element = Bloomberglp.Blpapi.Element;
using Event = Bloomberglp.Blpapi.Event;
using EventHandler = Bloomberglp.Blpapi.EventHandler;
using EventQueue = Bloomberglp.Blpapi.EventQueue;
using Message = Bloomberglp.Blpapi.Message;
using Name = Bloomberglp.Blpapi.Name;
using Request = Bloomberglp.Blpapi.Request;
using Service = Bloomberglp.Blpapi.Service;
using Session = Bloomberglp.Blpapi.Session;
using SessionOptions = Bloomberglp.Blpapi.SessionOptions;
using Subscription = Bloomberglp.Blpapi.Subscription;

namespace Bloomberglp.Blpapi.Examples
{
    class SimpleBlockingRequestExample
    {
        private Name LAST_PRICE = new Name("LAST_PRICE");


        public static void Main(String[] args)
        {
            SimpleBlockingRequestExample example = new SimpleBlockingRequestExample();
            example.run(args);
        }

        private void run(String[] args)
        {
            String serverHost = "localhost";
            int serverPort = 8194;

            SessionOptions sessionOptions = new SessionOptions();
            sessionOptions.ServerHost = serverHost;
            sessionOptions.ServerPort = serverPort;

            System.Console.WriteLine("Connecting to " + serverHost + ":" + serverPort);
            Session session = new Session(sessionOptions,
                new EventHandler(processEvent));
            if (!session.Start())
            {
                System.Console.Error.WriteLine("Failed to start session.");
                return;
            }
            if (!session.OpenService("//blp/mktdata"))
            {
                System.Console.Error.WriteLine("Failed to open //blp/mktdata");
                return;
            }
            if (!session.OpenService("//blp/refdata"))
            {
                System.Console.Error.WriteLine("Failed to open //blp/refdata");
                return;
            }

            System.Console.WriteLine("Subscribing to IBM US Equity");
            Subscription s = new Subscription("IBM US Equity", "LAST_PRICE", "");
            List<Subscription> subscriptions = new List<Subscription>();
            subscriptions.Add(s);
            session.Subscribe(subscriptions);

            System.Console.WriteLine("Requesting reference data IBM US Equity");
            Service refDataService = session.GetService("//blp/refdata");
            Request request = refDataService.CreateRequest("ReferenceDataRequest");
            request.GetElement("securities").AppendValue("IBM US Equity");
            request.GetElement("fields").AppendValue("DS002");

            EventQueue eventQueue = new EventQueue();
            session.SendRequest(request, eventQueue, null);
            while (true)
            {
                Event eventObj = eventQueue.NextEvent();

                foreach (Message msg in eventObj)
                {
                    System.Console.WriteLine(msg);
                }
                if (eventObj.Type == Event.EventType.RESPONSE)
                {
                    break;
                }
            }
            
            // wait for enter key to exit application
            System.Console.Read();
            System.Console.WriteLine("Exiting");
        }

        public void processEvent(Event eventObj, Session session)
        {
            try
            {
                if (eventObj.Type == Event.EventType.SUBSCRIPTION_DATA)
                {
                    foreach (Message msg in eventObj)
                    {
                        if (msg.HasElement(LAST_PRICE))
                        {
                            Element field = msg.GetElement(LAST_PRICE);
                            System.Console.WriteLine(eventObj.Type
                                + ": " + field.Name +
                                " = " + field.GetValueAsString());
                        }
                    }
                }
            }
            catch (Exception e)
            {
                System.Console.WriteLine(e.ToString());
            }
        }
    }
}
