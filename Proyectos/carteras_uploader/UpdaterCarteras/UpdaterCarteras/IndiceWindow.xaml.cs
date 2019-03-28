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
using System.Windows;
using System.Windows.Controls;
using System.Windows.Data;
using System.Windows.Documents;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using System.Windows.Shapes;
using System.Data.SqlClient;


namespace UpdaterCarteras
{
    /// <summary>
    /// Lógica de interacción para InstrumentoWindow.xaml
    /// </summary>
    public partial class IndiceWindow : Window
    {
        MainWindow main;

        public IndiceWindow(MainWindow main)
        {
            InitializeComponent();

            //Guardamos una referencia la menu principal para volver cuando se cierre la ventana
            this.main = main;
            string sql = "";
            SqlConnection connection = LibreriaFdo.ConectDatabaseUser("Puyehue", "MesaInversiones", "usrConsultaComercial", "Comercial1w");

            
            //Llenamos las combobox
            sql = "select distinct moneda from indices_estatica where moneda is not null";
            List<object> lista_moneda = LibreriaFdo.GetListSQL(connection, sql);
            foreach (string cod in lista_moneda)
            {
                ComboBox_Moneda.Items.Add((string)cod);
            }

            sql = "select distinct zona from indices_estatica where zona is not null";
            List<object> lista_zona = LibreriaFdo.GetListSQL(connection, sql);
            foreach (string cod in lista_zona)
            {
                ComboBox_Zona.Items.Add((string)cod);
            }

            sql = "select distinct renta from indices_estatica where renta is not null";
            List<object> lista_renta = LibreriaFdo.GetListSQL(connection, sql);
            foreach (string cod in lista_renta)
            {
                ComboBox_Renta.Items.Add((string)cod);
            }

            //Cerramos la conexion
            LibreriaFdo.DisconnectDatabase(connection);
        }


        /// <summary>
        ///Sube el nuevo indice a la base de datos
        /// </summary>
        /// 

        private void Boton_Upload_Click(object sender, RoutedEventArgs e)
        {
            //Obtenemos los datos de input del usuario
            string ticker = this.TextBox_Ticker.Text;
            string nombre_index = this.TextBox_Nombre_Index.Text;
            string moneda = this.ComboBox_Moneda.Text;
            string zona = this.ComboBox_Zona.Text;
            string renta = this.ComboBox_Renta.Text;
            // Obtenemos el index_id, por convencion seguimos n+1
            SqlConnection connection = LibreriaFdo.ConectDatabaseUser("Puyehue", "MesaInversiones", "usrConsultaComercial", "Comercial1w");
            string sql = "select top 1 index_id from indices_estatica order by index_id desc";
            int index_id = (int)LibreriaFdo.GetValueSQL(connection, sql) + 1;
            LibreriaFdo.DisconnectDatabase(connection);
            //Insertamos el nuevo indice en la tabla estatica
            connection = LibreriaFdo.ConectDatabaseUser("Puyehue", "MesaInversiones", "usrConsultaComercial", "Comercial1w");
            string insert_statement = "INSERT into Indices_Estatica (Index_Id, Ticker, Moneda, Nombre_Index, Zona, Renta) VALUES (@Index_Id, @Ticker, @Moneda, @Nombre_Index, @Zona, @Renta)";
            SqlCommand command = new SqlCommand(insert_statement);
            command.Connection = connection;
            command.Parameters.AddWithValue("@Index_Id", index_id);
            command.Parameters.AddWithValue("@Ticker", ticker);
            command.Parameters.AddWithValue("@Nombre_Index", nombre_index);
            command.Parameters.AddWithValue("@Moneda", moneda);
            command.Parameters.AddWithValue("@Zona", zona);
            command.Parameters.AddWithValue("@Renta", renta);
            try
            {
                int recordsAffected = command.ExecuteNonQuery();
            }
            catch (Exception ex)
            {
                MessageBox.Show(ex.ToString());
            }
            LibreriaFdo.DisconnectDatabase(connection);

            // En caso de que se quiera subir toda la historia descargamos de Bloomberg
            if (this.checkBox_historia.IsChecked == true)
            {
                // Seteamos las fechas de inicio y fin
                DateTime fecha_inicio = Convert.ToDateTime("01/01/2011");
                DateTime fecha_fin = DateTime.Today;
                string moneda_bbl = "";
                // Transformamos las monedas al formato de Bloomberg
                if (moneda == "$") { moneda_bbl = "CLP"; }
                else if (moneda == "US$") { moneda_bbl = "USD"; }


                // Mostramos una ventana de espera
                WaitWindow pleaseWait = new WaitWindow();
                pleaseWait.Show();

                // Descargamos los datos historicos
                List<object[]> data_raw = LibreriaFdo.GetHistoricalBBL(ticker, moneda_bbl, fecha_inicio, fecha_fin);
                // Obtenemos la ultima fecha que Bloomberg tiene datos, por convencion mantenemos el valor flat hasta la fecha de inicio.
                DateTime first_date = (DateTime)data_raw[0][0];
                double first_val = (double)data_raw[0][1];
                connection = LibreriaFdo.ConectDatabaseUser("Puyehue", "MesaInversiones", "usrConsultaComercial", "Comercial1w");
                insert_statement = "INSERT into Indices_Dinamica (Fecha, Index_Id, Valor) VALUES (@Fecha, @Index_Id, @Valor)";
                List<DateTime> weekdays = LibreriaFdo.WeekdayDates(fecha_inicio, first_date);
                foreach (DateTime fecha in weekdays)
                {
                command = new SqlCommand(insert_statement);
                command.Connection = connection;
                command.Parameters.AddWithValue("@Fecha", fecha);
                command.Parameters.AddWithValue("@Index_Id", index_id);
                command.Parameters.AddWithValue("@Valor", first_val);
                try
                {
                    int recordsAffected = command.ExecuteNonQuery();
                }
                catch (Exception ex)
                {
                    MessageBox.Show(ex.ToString());
                }
                }

                //Luego insertamos los datos de Bloomberg
                    foreach (object[]dia in data_raw)
                {
                    if (((DateTime)dia[0]).DayOfWeek != DayOfWeek.Sunday && ((DateTime)dia[0]).DayOfWeek != DayOfWeek.Saturday)
                    {
                        command = new SqlCommand(insert_statement);
                        command.Connection = connection;
                        command.Parameters.AddWithValue("@Fecha", dia[0]);
                        command.Parameters.AddWithValue("@Index_Id", index_id);
                        command.Parameters.AddWithValue("@Valor", dia[1]);
                        try
                        {
                            int recordsAffected = command.ExecuteNonQuery();
                        }
                        catch (Exception ex)
                        {
                            MessageBox.Show(ex.ToString());
                        }
                    }
                }
                LibreriaFdo.DisconnectDatabase(connection);
                //Cerramos la ventana de espera
                pleaseWait.Close();
            }
                 
            this.TextBox_Ticker.Text = "";
            this.TextBox_Nombre_Index.Text = "";
            this.ComboBox_Moneda.Text = "";
            MessageBox.Show("Indice agregado exitosamente con index_id numero " + index_id.ToString() + ".");

            //Cerramos la ventana
            this.Close();
        }
        private void Window_Closed(object sender, EventArgs e)
        {
            //Cuando se cierra volvemos al menu principal
            main.Show();
        }


    }



    }
