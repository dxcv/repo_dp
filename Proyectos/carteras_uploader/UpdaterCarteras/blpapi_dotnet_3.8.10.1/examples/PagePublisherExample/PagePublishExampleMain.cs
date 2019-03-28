using System;
using System.Collections.Generic;
using System.Text;

namespace Bloomberglp.Blpapi.Examples
{
	class PagePublishExampleMain
	{
		static void Main(string[] args)
		{
			System.Console.WriteLine("TestPublishExample");
			PagePublishExample example = new PagePublishExample();
			example.run(args);

			Console.WriteLine("Press <ENTER> to terminate.");
			Console.ReadLine();

		}
				
	}
}
