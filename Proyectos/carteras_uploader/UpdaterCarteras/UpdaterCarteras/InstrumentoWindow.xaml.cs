/*     
Created on Thu Dic 05 11:00:00 2016      
@author: Fernando Suarez      
*/
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
    public partial class InstrumentoWindow : Window
    {
        MainWindow main;

        public InstrumentoWindow(MainWindow main)
        {
            InitializeComponent();

            //Guardamos una referencia la menu principal para volver cuando se cierre la ventana
            this.main = main;
            string sql = "";
            SqlConnection connection = LibreriaFdo.ConectDatabaseUser("Puyehue", "MesaInversiones", "usrConsultaComercial", "Comercial1w");


            //Llenamos las combobox
            sql = "select distinct codigo_emi from emisores where codigo_emi is not null";
            List<object> lista_cod_emi = LibreriaFdo.GetListSQL(connection, sql);
            foreach (string cod in lista_cod_emi)
            {
                ComboBox_Codigo_Emi.Items.Add((string)cod);
            }


            sql = "select distinct nombre_instrumento from instrumentos where nombre_instrumento is not null";
            List<object> lista_nombres = LibreriaFdo.GetListSQL(connection, sql);
            foreach (string nombre in lista_nombres)
            {
                ComboBox_Nombre_Instrumento.Items.Add((string)nombre);
            }

            sql = "select distinct tipo_instrumento from instrumentos where tipo_instrumento is not null";
            List<object> lista_tipos = LibreriaFdo.GetListSQL(connection, sql);
            foreach (string tipo in lista_tipos)
            {
                ComboBox_Tipo_Instrumento.Items.Add((string)tipo);
            }


            sql = "select distinct riesgo from instrumentos where riesgo is not null";
            List<object> lista_riesgo = LibreriaFdo.GetListSQL(connection, sql);
            foreach (string riesgo in lista_riesgo)
            {
                ComboBox_Riesgo.Items.Add((string)riesgo);
            }

            sql = "select distinct zona from instrumentos where zona is not null";
            List<object> lista_zona = LibreriaFdo.GetListSQL(connection, sql);
            foreach (string zona in lista_zona)
            {
                ComboBox_Zona.Items.Add((string)zona);
            }

            sql = "select distinct renta from instrumentos where renta is not null";
            List<object> lista_renta = LibreriaFdo.GetListSQL(connection, sql);
            foreach (string renta in lista_renta)
            {
                ComboBox_Renta.Items.Add((string)renta);
            }

            //Cerramos la conexion
            LibreriaFdo.DisconnectDatabase(connection);
        }

        private void Boton_Upload_Click(object sender, RoutedEventArgs e)
        {
            string codigo_ins = this.TextBox_Codigo_Ins.Text;
            string codigo_emi = this.ComboBox_Codigo_Emi.Text;
            string nombre_instrumento = this.ComboBox_Nombre_Instrumento.Text;
            string tipo_instrumento = this.ComboBox_Tipo_Instrumento.Text;
            string riesgo = this.ComboBox_Riesgo.Text;
            string zona = this.ComboBox_Zona.Text;
            string renta = this.ComboBox_Renta.Text;
            string yesterday = LibreriaFdo.PreviousWorkDay(DateTime.Today).ToString("yyyy-MM-dd");

            SqlConnection connection = LibreriaFdo.ConectDatabaseUser("Puyehue", "MesaInversiones", "usrConsultaComercial", "Comercial1w");
            SqlCommand command;

            // caso en que es un ins del latam ig

            if (this.checkBox_Es_LATAM_IG.IsChecked == true)
            {
                string master_query = "select top 1 LTRIM(RTRIM(TICKERBLOOM)) AS ticker from master_instrumentos where codigo_ins = 'autocodins'";
                master_query = master_query.Replace("autocodins", codigo_ins);
                string ticker = (string)LibreriaFdo.GetValueSQL(connection, master_query);
                ticker += " Corp";
                string codigo_ins_bbl = LibreriaFdo.GetFieldBBL(ticker, "ID_CUSIP");
                codigo_ins_bbl = codigo_ins_bbl.Substring(0, codigo_ins_bbl.Length - 1);
                

                string zc_query_2 = "select top 1 codigo_ins from zhis_carteras_bmk where codigo_ins = 'autocodins'";
                zc_query_2 = zc_query_2.Replace("autocodins", codigo_ins_bbl);
                string check_ticker = "";
                try {
                    check_ticker = (string)LibreriaFdo.GetValueSQL(connection, zc_query_2);
                }
                catch (Exception ex) { MessageBox.Show(ex.ToString()); }

                // si esta en el bmk
                if (check_ticker != null)
                {

                    //borramos emisor antiguo
                    string delete_statement = "DELETE FROM Instrumentos WHERE codigo_ins = 'autocodins'";
                    delete_statement = delete_statement.Replace("autocodins", codigo_ins_bbl);

                    command = new SqlCommand(delete_statement);
                    command.Connection = connection;
                    try
                    {
                        int recordsAffected = command.ExecuteNonQuery();
                    }
                    catch (Exception ex)
                    {
                        MessageBox.Show(ex.ToString());
                    }



                    //borramos map antiguo
                    delete_statement = "DELETE FROM Mapping_BBL_BCS WHERE codigo_ins = 'autocodins'";
                    delete_statement = delete_statement.Replace("autocodins", codigo_ins_bbl);

                    command = new SqlCommand(delete_statement);
                    command.Connection = connection;
                    try
                    {
                        int recordsAffected2 = command.ExecuteNonQuery();
                    }
                    catch (Exception ex)
                    {
                        MessageBox.Show(ex.ToString());
                    }

                }

                else {


            
            ticker = codigo_ins_bbl + " Corp";
            string nombre_index =  LibreriaFdo.GetFieldBBL(ticker, "SECURITY_NAME");
            string moneda = "US$";
            string sql = "select top 1 index_id from indices_estatica order by index_id desc";
            int index_id = (int)LibreriaFdo.GetValueSQL(connection, sql) + 1;
            string insert_statement_st = "INSERT into Indices_Estatica (Index_Id, Ticker, Moneda, Nombre_Index, Zona, Renta) VALUES (@Index_Id, @Ticker, @Moneda, @Nombre_Index, @Zona, @Renta)";
            command = new SqlCommand(insert_statement_st);
            command.Connection = connection;
            command.Parameters.AddWithValue("@Index_Id", index_id);
            command.Parameters.AddWithValue("@Ticker", ticker);
            command.Parameters.AddWithValue("@Nombre_Index", nombre_index);
            command.Parameters.AddWithValue("@Moneda", moneda);
            command.Parameters.AddWithValue("@Zona", zona);
            command.Parameters.AddWithValue("@Renta", renta);
            try
            {
                int recordsAffected6 = command.ExecuteNonQuery();
            }
            catch (Exception ex)
            {
                MessageBox.Show(ex.ToString());
            }

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
            string insert_statement_hist = "INSERT into Indices_Dinamica (Fecha, Index_Id, Valor) VALUES (@Fecha, @Index_Id, @Valor)";
            List<DateTime> weekdays = LibreriaFdo.WeekdayDates(fecha_inicio, first_date);
            foreach (DateTime fecha in weekdays)
            {
            command = new SqlCommand(insert_statement_hist);
            command.Connection = connection;
            command.Parameters.AddWithValue("@Fecha", fecha);
            command.Parameters.AddWithValue("@Index_Id", index_id);
            command.Parameters.AddWithValue("@Valor", first_val);
            try
            {
                int recordsAffected8 = command.ExecuteNonQuery();
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
                    command = new SqlCommand(insert_statement_hist);
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

            //Cerramos la ventana de espera
            pleaseWait.Close();
                 
                }


                //actualizamos zhis bmk
                string update_statement = "UPDATE ZHIS_Carteras_Bmk SET codigo_ins = 'autocodins' WHERE codigo_ins = 'autocodinsbbl'";
                update_statement = update_statement.Replace("autocodinsbbl", codigo_ins_bbl);
                update_statement = update_statement.Replace("autocodins", codigo_ins);

                command = new SqlCommand(update_statement);
                command.Connection = connection;
                try
                {
                    int recordsAffected11 = command.ExecuteNonQuery();
                }
                catch (Exception ex)
                {
                    MessageBox.Show(ex.ToString());
                }


                // insertamos map nuevo
                codigo_ins_bbl = codigo_ins_bbl + " Corp";
                string insert_statement_map = "INSERT into Mapping_BBL_BCS (Codigo_Ins, Codigo_Ins_BBL) VALUES (@Codigo_Ins, @Codigo_Ins_BBL)";
                command = new SqlCommand(insert_statement_map);
                command.Connection = connection;
                command.Parameters.AddWithValue("@Codigo_Ins", codigo_ins);
                command.Parameters.AddWithValue("@Codigo_Ins_BBL", codigo_ins_bbl);
                try
                {
                    int recordsAffected5 = command.ExecuteNonQuery();
                }
                catch (Exception ex)
                {
                    MessageBox.Show(ex.ToString());
                }


            }
            string insert_statement = "INSERT into Instrumentos (Codigo_Emi, Codigo_Ins, Nombre_Instrumento, Tipo_Instrumento, Riesgo, Zona, Renta) VALUES (@Codigo_Emi, @Codigo_Ins, @Nombre_Instrumento, @Tipo_Instrumento, @Riesgo, @Zona, @Renta)";
            command = new SqlCommand(insert_statement);
            command.Connection = connection;
            command.Parameters.AddWithValue("@Codigo_Ins", codigo_ins);
            command.Parameters.AddWithValue("@Codigo_Emi", codigo_emi);
            command.Parameters.AddWithValue("@Nombre_Instrumento", nombre_instrumento);
            command.Parameters.AddWithValue("@Tipo_Instrumento", tipo_instrumento);
            command.Parameters.AddWithValue("@Riesgo", riesgo);
            command.Parameters.AddWithValue("@Zona", zona);
            command.Parameters.AddWithValue("@Renta", renta);
            try
            {
                int recordsAffected4 = command.ExecuteNonQuery();
                this.TextBox_Codigo_Ins.Text = "";
                this.ComboBox_Codigo_Emi.Text = "";
                this.ComboBox_Nombre_Instrumento.Text = "";
                this.ComboBox_Tipo_Instrumento.Text = "";
                this.ComboBox_Riesgo.Text = "";
                this.ComboBox_Zona.Text = "";
                this.ComboBox_Renta.Text = "";
                MessageBox.Show("Instrumento agregado exitosamente.");
            }
            catch (Exception ex)
            {
                MessageBox.Show(ex.ToString());
            }
            LibreriaFdo.DisconnectDatabase(connection);

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
