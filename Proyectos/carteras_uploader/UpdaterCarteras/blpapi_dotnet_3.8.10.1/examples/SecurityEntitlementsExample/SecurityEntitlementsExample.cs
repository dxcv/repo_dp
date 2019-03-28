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
using ArrayList = System.Collections.ArrayList;
using Session = Bloomberglp.Blpapi.Session;
using Name = Bloomberglp.Blpapi.Name;
using Event = Bloomberglp.Blpapi.Event;
using Message = Bloomberglp.Blpapi.Message;
using Service = Bloomberglp.Blpapi.Service;
using Identity = Bloomberglp.Blpapi.Identity;
using Request = Bloomberglp.Blpapi.Request;
using Element = Bloomberglp.Blpapi.Element;
using EventHandler = Bloomberglp.Blpapi.EventHandler;
using SessionOptions = Bloomberglp.Blpapi.SessionOptions;
using CorrrelationID = Bloomberglp.Blpapi.CorrelationID;
using EventQueue = Bloomberglp.Blpapi.EventQueue;
using System.Collections.Generic;

namespace Bloomberglp.Blpapi.Examples
{
	public class SecurityEntitlementsExample
	{
        private const string API_AUTH_SVC_NAME = "//blp/apiauth";
        private static readonly Name SECURITYENTITLEMENTS_RESPONSE = Name.GetName(
           "SecurityEntitlementsResponse");
        private string d_serverHost;
        private int d_serverPort;
        private List<string>  d_securities;
    

 	    public SecurityEntitlementsExample()
 	    {
		    d_serverHost = "localhost";
		    d_serverPort = 8194;
		    d_securities = new List<string>();
 	    }

	    public static void Main(String[] args)
        {
		    System.Console.WriteLine("SecurityEntitlements Example");
		    SecurityEntitlementsExample example = new SecurityEntitlementsExample();
            example.run(args);
            System.Console.WriteLine("Press ENTER to quit");
		    System.Console.Read();
	    }

	    private void run(String[] args)
        {		
		    if (!parseCommandLine(args)){
			    printUsage();
			    System.Environment.Exit(-1);
		    }
            SessionOptions sessionOptions = new SessionOptions();
            sessionOptions.ServerHost = d_serverHost;
            sessionOptions.ServerPort = d_serverPort;

            System.Console.WriteLine("Connecting to " + d_serverHost + ":" 
                + d_serverPort);
            Session session = new Session(sessionOptions);
            if (!session.Start()) {
                System.Console.WriteLine("Failed to start session.");
                return;
            }
            if (!session.OpenService(API_AUTH_SVC_NAME)) {
			    System.Console.WriteLine("Failed to open service: " + API_AUTH_SVC_NAME);
			    System.Environment.Exit(-1);
		    }
            Service apiAuthSvc = session.GetService(API_AUTH_SVC_NAME);
       	    EventQueue eventQueue = new EventQueue();	
		    CorrelationID correlator = new CorrelationID(10);
		    Request request = apiAuthSvc.CreateRequest("SecurityEntitlementsRequest");
		    Element securities = request.GetElement("securities");
            for (int i = 0; i < d_securities.Count; ++i) {
                securities.AppendValue(d_securities[i]);
            }        
            
		    session.SendRequest(request, eventQueue, correlator);
    		
		    Event eventObj = eventQueue.NextEvent(5000*60);		
		    if (eventObj.Type == Event.EventType.RESPONSE ||
					    eventObj.Type == Event.EventType.REQUEST_STATUS) {
                foreach (Message msg in eventObj) {
                    if (msg.MessageType.Equals(SECURITYENTITLEMENTS_RESPONSE))
                    {
                        Element eidData = msg.GetElement("eidData");
                        if (eidData.NumValues == 0)
                        {
                            printEvent(eventObj);
                        }
                        else
                        {
                            for (int i = 0; i < eidData.NumValues; ++i)
                            {
                                Element item = eidData.GetValueAsElement(i);
                                int status = item.GetElementAsInt32("status");
                                System.Console.Write((String)d_securities[i] + "\t:\t");
                                if (0 == status)
                                {
                                    Element eids = item.GetElement("eids");
                                    for (int j = 0; j < eids.NumValues; ++j)
                                    {
                                        System.Console.Write(eids.GetValueAsInt32(j) + " ");
                                    }
                                }
                                else
                                {   // anything nonzero, means we failed to retrieve eids for security
                                    System.Console.Write("Failed (" + status + ")");
                                }
                                System.Console.WriteLine();
                            }
                            session.Cancel(correlator);
                        }
                    }
			    }
		    } else {
			    printEvent(eventObj);
		    }  
		    session.Cancel(correlator);
        }

        private bool parseCommandLine(String[] args)
        {
            for (int i = 0; i < args.Length; ++i) 
            {
                if (string.Compare(args[i], "-s", true) == 0) 
                {            
                    d_securities.Add(args[i+1]);
                }
                else if (string.Compare(args[i], "-ip", true) == 0) 
                {
                    d_serverHost = args[i+1];
                }
                else if (string.Compare(args[i], "-p", true) == 0) 
                {            
                    d_serverPort = int.Parse(args[i+1]);
                }
                else if (string.Compare(args[i], "-h", true) == 0) 
                {             
                    return false;
                }
            }
        
            if (d_securities.Count <= 0) {
        	    d_securities.Add("IBM US Equity");
            }

            return true;
        }

        private void printUsage()
        {
            System.Console.WriteLine("	SecurityEntitlements Example");
            System.Console.WriteLine("		[-ip <ipAddress	= localhost>   ]");
            System.Console.WriteLine("		[-p  <tcpPort	= 8194>        ]");
            System.Console.WriteLine("		[-s	 <security = IBM US Equity>]");
            System.Console.WriteLine("Press ENTER to quit");

        }

        private void printEvent(Event eventObj)
        {
            foreach (Message msg in eventObj)
            {
                CorrelationID correlationId = msg.CorrelationID;
                if (correlationId != null)
                {
                    System.Console.WriteLine("Correlator: " + correlationId);
                }

                Service service = msg.Service;
                if (service != null)
                {
                    System.Console.WriteLine("Service: " + service.Name);
                }
                System.Console.WriteLine(msg);
            }
        }
    }
}
