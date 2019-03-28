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
using System.Diagnostics;
using UpdaterCarteras;

namespace UpdaterCarteras
{
    /// <summary>
    /// Lógica de interacción para EmisorWindow.xaml
    /// </summary>
    public partial class EmisorWindow : Window
    {
        MainWindow main;
        public EmisorWindow(MainWindow main)
        {
            InitializeComponent();

            //Guardamos una referencia la menu principal para volver cuando se cierre la ventana
            this.main = main;

            //LLenamos las combobox 

            string sql = "select distinct nombre_emisor from emisores where nombre_emisor is not null";
            SqlConnection connection = LibreriaFdo.ConectDatabaseUser("Puyehue", "MesaInversiones", "usrConsultaComercial", "Comercial1w");
            List<object> lista_nombres = LibreriaFdo.GetListSQL(connection, sql);
            foreach (string nombre in lista_nombres)
            {
                ComboBox_Nombre_Emisor.Items.Add((string)nombre);
            }
            LibreriaFdo.DisconnectDatabase(connection);


            sql = "select distinct sector from emisores where sector is not null";
            connection = LibreriaFdo.ConectDatabaseUser("Puyehue", "MesaInversiones", "usrConsultaComercial", "Comercial1w");
            List<object> lista_sectores = LibreriaFdo.GetListSQL(connection, sql);
            foreach (string sector in lista_sectores)
            {
                ComboBox_Sector.Items.Add((string)sector);
            }
            LibreriaFdo.DisconnectDatabase(connection);

            sql = "select distinct pais_emisor from emisores where pais_emisor is not null";
            connection = LibreriaFdo.ConectDatabaseUser("Puyehue", "MesaInversiones", "usrConsultaComercial", "Comercial1w");
            List<object> lista_paises = LibreriaFdo.GetListSQL(connection, sql);
            foreach (string pais in lista_paises)
            {
                ComboBox_Pais_Emisor.Items.Add((string)pais);
            }
            LibreriaFdo.DisconnectDatabase(connection);
        }

        private void Boton_Upload_Click(object sender, RoutedEventArgs e)
        {
            string codigo_emi = this.TextBox_Codigo_Emi.Text;
            string nombre_emisor = this.ComboBox_Nombre_Emisor.Text;
            string sector = this.ComboBox_Sector.Text;
            string pais_emisor = this.ComboBox_Pais_Emisor.Text;
            string yesterday = LibreriaFdo.PreviousWorkDay(DateTime.Today).ToString("yyyy-MM-dd");
            SqlConnection connection = LibreriaFdo.ConectDatabaseUser("Puyehue", "MesaInversiones", "usrConsultaComercial", "Comercial1w");
            SqlCommand command;
            // caso en que es un ins del latam ig

             if (this.checkBox_Es_LATAM_IG.IsChecked == true)
                {
                // Vamos a ver si el emisor esta en el bmk
                string zc_query = "select top 1 codigo_ins from lagunillas_zhis_carteras where fecha = 'autodate' and codigo_fdo = 'LATAM IG' and codigo_emi = 'autocodemi'";
                zc_query = zc_query.Replace("autodate", yesterday);
                zc_query = zc_query.Replace("autocodemi", codigo_emi);
                string codigo_ins = (string) LibreriaFdo.GetValueSQL(connection, zc_query);

                string master_query = "select top 1 LTRIM(RTRIM(TICKERBLOOM)) AS ticker from master_instrumentos where codigo_ins = 'autocodins'";
                master_query = master_query.Replace("autocodins", codigo_ins);
                string ticker = (string) LibreriaFdo.GetValueSQL(connection, master_query);

                ticker += " Corp";

                string codigo_ins_bbl = LibreriaFdo.GetFieldBBL(ticker, "ID_CUSIP");
                codigo_ins_bbl = codigo_ins_bbl.Substring(0, codigo_ins_bbl.Length - 1);


                string zc_query_2 = "select top 1 codigo_ins from zhis_carteras_bmk where codigo_ins = 'autocodins'";
                zc_query_2 = zc_query_2.Replace("autocodins", codigo_ins_bbl);
                string check_ticker = "";
                try { check_ticker = (string)LibreriaFdo.GetValueSQL(connection, zc_query_2); }
                catch (Exception ex) { }


                // si esta en el bmk
                if (check_ticker != "") {

                    //borramos emisor antiguo
                    string delete_statement= "DELETE FROM Emisores WHERE codigo_emi = 'autocodemi'";
                    delete_statement = delete_statement.Replace("autocodemi", codigo_ins_bbl);

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
                
            }

            LibreriaFdo.DisconnectDatabase(connection);
            SqlConnection connection2 = LibreriaFdo.ConectDatabaseUser("Puyehue", "MesaInversiones", "usrConsultaComercial", "Comercial1w");
            string insert_statement = "INSERT into Emisores (Codigo_Emi,Nombre_Emisor,Sector,Pais_Emisor) VALUES (@Codigo_Emi,@Nombre_Emisor,@Sector,@Pais_Emisor)";
            command = new SqlCommand(insert_statement);
            command.Connection = connection2;
            command.Parameters.AddWithValue("@Codigo_Emi", codigo_emi);
            command.Parameters.AddWithValue("@Nombre_Emisor", nombre_emisor);
            command.Parameters.AddWithValue("@Sector", sector);
            command.Parameters.AddWithValue("@Pais_Emisor", pais_emisor);
            try
            {
                int recordsAffected3 = command.ExecuteNonQuery();
                this.TextBox_Codigo_Emi.Text = "";
                this.ComboBox_Nombre_Emisor.Text = "";
                this.ComboBox_Sector.Text = "";
                this.ComboBox_Pais_Emisor.Text = "";
                MessageBox.Show("Emisor agregado exitosamente.");
            }
            catch(Exception ex)
            {
                MessageBox.Show(ex.ToString());
            }
           
            LibreriaFdo.DisconnectDatabase(connection2);
            this.Close();
        }


        private void Window_Closed(object sender, EventArgs e)
        {
            //Cuando se cierra volvemos al menu principal
            main.Show();
        }

    }
}
