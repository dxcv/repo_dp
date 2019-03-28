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
    /// Lógica de interacción para EstrategiaWindow.xaml
    /// </summary>
    public partial class EstrategiaWindow : Window
    {
        MainWindow main;

        public EstrategiaWindow(MainWindow main)
        {
            InitializeComponent();

            //Guardamos una referencia la menu principal para volver cuando se cierre la ventana
            this.main = main;

            //Llenamos la combobox de fondos
            String sql = "";
            SqlConnection connection = LibreriaFdo.ConectDatabaseUser("Puyehue", "MesaInversiones", "usrConsultaComercial", "Comercial1w");

            // Fondos
            sql = "select distinct codigo_fdo from fondosir where active = 1";
            List<object> lista_cod_fdo = LibreriaFdo.GetListSQL(connection, sql);
            foreach (string cod in lista_cod_fdo)
            {
                ComboBox_Codigo_Fdo.Items.Add((string)cod);
            }

            // Estrategia
            sql = "select distinct estrategia from estrategias";
            List<object> lista_estrategias = LibreriaFdo.GetListSQL(connection, sql);
            foreach (string cod in lista_estrategias)
            {
                ComboBox_Estrategia.Items.Add((string)cod);
            }
            LibreriaFdo.DisconnectDatabase(connection);
        }

        private void Boton_Upload_Click(object sender, RoutedEventArgs e)
        {
            string codigo_fdo = this.ComboBox_Codigo_Fdo.Text;
            string codigo_ins = this.ComboBox_Codigo_Ins.Text;
            string codigo_emi = this.ComboBox_Codigo_Emi.Text;
            string estrategia = this.ComboBox_Estrategia.Text;

            SqlConnection connection = LibreriaFdo.ConectDatabaseUser("Puyehue", "MesaInversiones", "usrConsultaComercial", "Comercial1w");
            string insert_statement = "INSERT into Estrategias (Codigo_Fdo, Codigo_Emi, Codigo_Ins, Estrategia) VALUES (@Codigo_Fdo, @Codigo_Emi, @Codigo_Ins, @Estrategia)";
            SqlCommand command = new SqlCommand(insert_statement);
            command.Connection = connection;
            command.Parameters.AddWithValue("@Codigo_Fdo", codigo_fdo);
            command.Parameters.AddWithValue("@Codigo_Emi", codigo_emi);
            command.Parameters.AddWithValue("@Codigo_Ins", codigo_ins);
            command.Parameters.AddWithValue("@Estrategia", estrategia);
            try
            {
                int recordsAffected = command.ExecuteNonQuery();
                MessageBox.Show("Estrategia asociada exitosamente.");
            }
            catch (Exception ex)
            {

                try
                {
                    string update_statement = "UPDATE Estrategias SET Estrategia = @Estrategia WHERE Codigo_Fdo = @Codigo_Fdo AND Codigo_Emi = @Codigo_Emi AND Codigo_INS = @Codigo_Ins";
                    command = new SqlCommand(update_statement);
                    command.Connection = connection;
                    command.Parameters.AddWithValue("@Codigo_Fdo", codigo_fdo);
                    command.Parameters.AddWithValue("@Codigo_Emi", codigo_emi);
                    command.Parameters.AddWithValue("@Codigo_Ins", codigo_ins);
                    command.Parameters.AddWithValue("@Estrategia", estrategia);
                    int recordsAffected = command.ExecuteNonQuery();
                    MessageBox.Show("Estrategia asociada exitosamente.");
                }
                catch (Exception ex2)
                {
                    MessageBox.Show(ex2.ToString());
                }
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

        private void ComboBox_Codigo_Fdo_SelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            String fecha_prev = System.DateTime.Now.AddDays(-1).ToString(@"yyyy-MM-dd");
            String sql = "";
            SqlConnection connection = LibreriaFdo.ConectDatabaseUser("Puyehue", "MesaInversiones", "usrConsultaComercial", "Comercial1w");
            // Emisores
            sql = "select distinct codigo_emi from ZHIS_Carteras_Main where fecha = '" + fecha_prev + "' and codigo_fdo = '" + this.ComboBox_Codigo_Fdo.SelectedItem.ToString() + "'";
            List<object> lista_cod_emi = LibreriaFdo.GetListSQL(connection, sql);
            foreach (string cod in lista_cod_emi)
            {
                ComboBox_Codigo_Emi.Items.Add((string)cod);
            }
            // Desconectamos de la base de datos
            LibreriaFdo.DisconnectDatabase(connection);
        }

        private void ComboBox_Codigo_Emi_SelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            String fecha_prev = System.DateTime.Now.AddDays(-1).ToString(@"yyyy-MM-dd");
            String sql = "";
            SqlConnection connection = LibreriaFdo.ConectDatabaseUser("Puyehue", "MesaInversiones", "usrConsultaComercial", "Comercial1w");
            // Instrumentos
            sql = "select distinct codigo_ins from ZHIS_Carteras_Main where fecha = '" + fecha_prev + "' and codigo_fdo = '" + this.ComboBox_Codigo_Fdo.SelectedItem.ToString() + "' and codigo_emi = '" + this.ComboBox_Codigo_Emi.SelectedItem.ToString() + "'";
            List<object> lista_instrumentos = LibreriaFdo.GetListSQL(connection, sql);
            foreach (string cod in lista_instrumentos)
            {
                ComboBox_Codigo_Ins.Items.Add((string)cod);
            }
            LibreriaFdo.DisconnectDatabase(connection);

        }
    }
}
