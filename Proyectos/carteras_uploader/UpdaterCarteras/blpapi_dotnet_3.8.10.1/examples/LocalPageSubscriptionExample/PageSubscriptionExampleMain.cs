using System;
using System.Collections.Generic;
using System.Text;

namespace Bloomberglp.Blpapi.Examples
{
	class PageSubscriptionExampleMain
	{

		public static void Main(String[] args) 
		{
			System.Console.WriteLine("TestSubscriptionExample");
			PageSubscriptionExample example = new PageSubscriptionExample();
			example.run(args);
			Console.WriteLine("Press ENTER to quit");
			System.Console.ReadLine();
		}
	}
}
