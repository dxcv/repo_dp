//using System;
//using System.Collections.Generic;
//using System.Text;

//namespace Bloomberglp.Blpapi.Examples
//{
//    class PublishEventHandler:ProviderEventHandler 
//    {
//        public boolean processEvent(Event event, ProviderSession session)
//        {
//            ResolutionList resolutionList = new ResolutionList();
			
//            System.out.println("MyEventHandler::processEvent: " + event.eventType());
//            if(event.eventType() == EventType.TOPIC_STATUS)
//            {
//                MessageIterator iter = event.messageIterator();
//                while(iter.hasNext())
//                {
//                    Message msg = iter.next();
//                    if(msg.messageType() == Name.getName("TopicSubscribed"))
//                    {
//                        resolutionList.add(msg);
//                    }
//                }
				
//                if(resolutionList.size() > 0)
//                {
//                    session.resolveAsync(resolutionList);
//                }
//            }
//            else if(event.eventType() == EventType.RESOLUTION_STATUS)
//            {
//                MessageIterator iter = event.messageIterator();
//                while(iter.hasNext())
//                {
//                    Message msg = iter.next();
//                    if(msg.messageType() == Name.getName("ResolutionSuccess"))
//                    {
//                        g_topic = session.createTopic(msg);
//                        String resolvedTopic = msg.getElementAsString(Name.getName("resolvedTopic"));
//                        System.out.println("ResolvedTopic: " + resolvedTopic);
//                    }
//                }
//            }
			
//            return true;
//        }
//    }
//}
