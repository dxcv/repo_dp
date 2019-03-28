/// <summary>
///Created on Mon Dec 26 11:00:00 2016
///@author: Fernando Suarez
/// </summary>
/// 

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Data.SqlClient;
using System.Diagnostics;
using System.Windows.Controls;
using System.Windows;

//BBL
using Event = Bloomberglp.Blpapi.Event;
using Message = Bloomberglp.Blpapi.Message;
using Name = Bloomberglp.Blpapi.Name;
using Request = Bloomberglp.Blpapi.Request;
using Service = Bloomberglp.Blpapi.Service;
using Session = Bloomberglp.Blpapi.Session;
using SessionOptions = Bloomberglp.Blpapi.SessionOptions;
using Element = Bloomberglp.Blpapi.Element;

namespace UpdaterCarteras
{
    class LibreriaFdo
    {

        /// <summary>
        /// Se conecta a una base de datos con usuario y password
        /// </summary>
        public static SqlConnection ConectDatabaseUser(string server, string database, string username, string password)
        {
            string connetionString = "Data Source=" + server + ";Initial Catalog=" + database + ";User ID=" + username + ";Password=" + password;
            SqlConnection connection = new SqlConnection(connetionString);
            try
            {
                connection.Open();
            }
            catch (Exception ex)
            {
                MessageBox.Show(ex.ToString());
            }
            return connection;
        }

        /// <summary>
        /// En base a una conexion y una query obtine las tuplas en una tabla
        /// </summary>
        public static List<List<object>> GetTableSQL(SqlConnection connection, string query)
        {
            SqlCommand command = new SqlCommand(query, connection);
            SqlDataReader dataReader = command.ExecuteReader();
            List<List<object>> table = new List<List<object>>();
            int ncolumns = dataReader.FieldCount;
            while (dataReader.Read())
            {
                List<object> row = new List<object>();
                for (int i = 0; i < ncolumns; i++)
                {
                    row.Add(dataReader.GetValue(i));
                }
                table.Add(row);
            }
            dataReader.Close();
            command.Dispose();
            return table;
        }

        /// <summary>
        /// En base a una conexion y una query obtine las tuplas en una lista
        /// </summary>
        public static List<object> GetListSQL(SqlConnection connection, string query)
        {
            SqlCommand command = new SqlCommand(query, connection);
            SqlDataReader dataReader = command.ExecuteReader();
            List<object> table = new List<object>();
            int ncolumns = dataReader.FieldCount;
            while (dataReader.Read())
            {
                table.Add(dataReader.GetValue(0));
            }
            dataReader.Close();
            command.Dispose();
            return table;
        }

        /// <summary>
        /// En base a una conexion y una query obtiene un valor en forma de objeto
        /// </summary>
        public static object GetValueSQL(SqlConnection connection, string query)
        {
            SqlCommand command = new SqlCommand(query, connection);
            SqlDataReader dataReader = command.ExecuteReader();
            dataReader.Read();
            object val;
            try
            {
                val = dataReader.GetValue(0);
            }
            catch (Exception e) {

                val = null;
            }
            dataReader.Close();
            command.Dispose();
            return val;
        }

        /// <summary>
        /// Descarga informacion historica de Bloomberg
        /// </summary>
        public static List<object[]> GetHistoricalBBL(string ticker, string currency, DateTime start_date, DateTime end_date)
        {
            //Retornamos todo en una lista de tuplas con dos elementos: fecha y valor
            List<object[]> table = new List<object[]>();
            //Conectamos
            string serverHost = "localhost";
            int serverPort = 8194;
            SessionOptions sessionOptions = new SessionOptions();
            sessionOptions.ServerHost = serverHost;
            sessionOptions.ServerPort = serverPort;
            Session session = new Session(sessionOptions);
            bool sessionStarted = session.Start();
            session.OpenService("//blp/refdata");
            Service refDataService = session.GetService("//blp/refdata");
            Request request = refDataService.CreateRequest("HistoricalDataRequest");
            Element securities = request.GetElement("securities");
            securities.AppendValue(ticker); // Si quiero bajar varios hay que hacer mas appends
            Element fields = request.GetElement("fields");
            fields.AppendValue("PX_LAST"); // lo mismo para fields

            //Esta es la confirguracion por defecto para subir indices a la base de datos, se puede extender para otros usos
            request.Set("periodicityAdjustment", "ACTUAL");
            request.Set("periodicitySelection", "DAILY");
            request.Set("startDate", start_date.ToString("yyyyMMdd"));
            request.Set("endDate", end_date.ToString("yyyyMMdd"));
            request.Set("maxDataPoints", 10000000);
            request.Set("returnEids", true);
            request.Set("currency", currency);
            request.Set("nonTradingDayFillOption", "NON_TRADING_WEEKDAYS");
            request.Set("nonTradingDayFillMethod", "PREVIOUS_VALUE");
            session.SendRequest(request, null);
            Event eventObj = session.NextEvent();
            eventObj = session.NextEvent();
            eventObj = session.NextEvent();
            eventObj = session.NextEvent();
            foreach (Message msg in eventObj)
                {
                Element datos = msg.AsElement.GetElement("securityData").GetElement("fieldData"); //.GetElement("HistoricalDataResponse")
                  for(int i = 0; i < datos.NumValues; i++)
                {
                    try
                    {
                        double dato = datos.GetValueAsElement(i).GetElement("PX_LAST").GetValueAsFloat64();
                        DateTime fecha = Convert.ToDateTime(datos.GetValueAsElement(i).GetElement("date").GetValueAsString());
                        table.Add(new object[2] { fecha, dato });
                    }
                    catch (Exception ex)
                    {
                        //System.Console.WriteLine(ex.ToString());
                    }
                }
            }
            return table;
        }




        public static string GetFieldBBL(string ticker, string field)
        {
            string serverHost = "localhost";
            int serverPort = 8194;
            SessionOptions sessionOptions = new SessionOptions();
            sessionOptions.ServerHost = serverHost;
            sessionOptions.ServerPort = serverPort;
            Session session = new Session(sessionOptions);
            bool sessionStarted = session.Start();
            session.OpenService("//blp/refdata");
            Service refDataService = session.GetService("//blp/refdata");
            Request request = refDataService.CreateRequest("ReferenceDataRequest");
            Element securities = request.GetElement("securities");
            securities.AppendValue(ticker); // Si quiero bajar varios hay que hacer mas appends
            Element fields = request.GetElement("fields");
            fields.AppendValue(field); 
            session.SendRequest(request, null);
            Event eventObj = session.NextEvent();
            eventObj = session.NextEvent();
            eventObj = session.NextEvent();
            eventObj = session.NextEvent();
            string value = eventObj.ToList()[0].AsElement.Elements.ToList()[0].GetValueAsElement(0).Elements.ToList()[3].Elements.ToList()[0].GetValueAsString();
            
            return value;
        }




        public static List<DateTime> WeekdayDates(DateTime start_date, DateTime end_date)
        {
            List<DateTime> days_list = new List<DateTime>();
            for (DateTime date = start_date; date < end_date; date = date.AddDays(1))
            {
                if (date.DayOfWeek != DayOfWeek.Sunday && date.DayOfWeek != DayOfWeek.Saturday)
                    days_list.Add(date);
            }

            return days_list;
        }

        public static void DisconnectDatabase(SqlConnection connection)
        {
            connection.Close();
        }

        public static DateTime PreviousWorkDay(DateTime date)
        {
            do
            {
                date = date.AddDays(-1);
            }
            while (IsWeekend(date));

            return date;
        }

        private static bool IsWeekend(DateTime date)
        {
            return date.DayOfWeek == DayOfWeek.Saturday ||
                   date.DayOfWeek == DayOfWeek.Sunday;
        }


    }
}
