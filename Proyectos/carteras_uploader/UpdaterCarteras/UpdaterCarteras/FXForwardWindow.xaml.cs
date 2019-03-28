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
    public partial class FXForwardWindow : Window
    {
        MainWindow main;
        public FXForwardWindow(MainWindow main)
        {
            InitializeComponent();


            this.main = main;
            //Llenamos las combobox
            String sql = "";
            SqlConnection connection = LibreriaFdo.ConectDatabaseUser("Puyehue", "MesaInversiones", "usrConsultaComercial", "Comercial1w");

            // Fondos
            sql = "select distinct codigo_fdo from fondosir where active = 1";
            List<object> lista_cod_fdo = LibreriaFdo.GetListSQL(connection, sql);
            foreach (string cod in lista_cod_fdo)
            {
                ComboBox_Codigo_Fdo.Items.Add((string)cod);
            }

            // Emisores
            sql = "select distinct codigo_emi from emisores";
            List<object> lista_cod_emi = LibreriaFdo.GetListSQL(connection, sql);
            foreach (string cod in lista_cod_emi)
            {
                ComboBox_Codigo_Emi.Items.Add((string)cod);
            }

            // Monedas de compra
            sql = "select distinct moneda_compra from fwd_monedas_estatica";
            List<object> lista_monedas_compra = LibreriaFdo.GetListSQL(connection, sql);
            foreach (string cod in lista_monedas_compra)
            {
                ComboBox_Moneda_Compra.Items.Add((string)cod); 
            }
            
            // Monedas de venta
            sql = "select distinct moneda_venta from fwd_monedas_estatica";
            List<object> lista_monedas_venta = LibreriaFdo.GetListSQL(connection, sql);
            foreach (string cod in lista_monedas_venta)
            {
                ComboBox_Moneda_Venta.Items.Add((string)cod);
            }
            
            // Instrumentos sinteticos
            sql = "select distinct codigo_ins from instrumentos";
            List<object> lista_instrumentos_sinteticos = LibreriaFdo.GetListSQL(connection, sql);
            foreach (string cod in lista_instrumentos_sinteticos)
            {
                ComboBox_Instrumento_Sintetico.Items.Add((string)cod);
            }

            // Estrategia
            sql = "select distinct estrategia from fwd_monedas_estatica";
            List<object> lista_estrategias = LibreriaFdo.GetListSQL(connection, sql);
            foreach (string cod in lista_estrategias)
            {
                ComboBox_Estrategia.Items.Add((string)cod);
            }

            // Desconectamos de la base de datos
            LibreriaFdo.DisconnectDatabase(connection);

        }

        private void Window_Closed(object sender, EventArgs e)
        {
            //Cuando se cierra volvemos al menu principal
            main.Show();
        }

        private void setPrevDate(object sender, SelectionChangedEventArgs e)
        {
            DateTime fecha_vcto = ((DatePicker)sender).SelectedDate.Value;
            DatePicker_Fecha_Fix.SelectedDate = fecha_vcto.AddDays(-1);
        }

        private void Boton_Upload_Click(object sender, RoutedEventArgs e)
        {
            //Gatillamos el evento de carga de datos
            //Sacamos informacion de la interfaz grafica
            DateTime fecha_op = this.DatePicker_Fecha_Op.SelectedDate.Value;
            DateTime fecha_vcto = this.DatePicker_Fecha_Vcto.SelectedDate.Value;
            DateTime fecha_fix = this.DatePicker_Fecha_Fix.SelectedDate.Value;
            string codigo_fdo = this.ComboBox_Codigo_Fdo.Text;
            string codigo_emi = this.ComboBox_Codigo_Emi.Text;
            string moneda_compra = this.ComboBox_Moneda_Compra.Text;
            string moneda_venta = this.ComboBox_Moneda_Venta.Text;
            string instrumento_sintetico = this.ComboBox_Instrumento_Sintetico.Text;
            string estrategia = this.ComboBox_Estrategia.Text;
            float nominal_compra = float.Parse(this.TextBox_Nominal_Compra.Text);
            float nominal_venta = float.Parse(this.TextBox_Nominal_Venta.Text);
            float precio_pactado = float.Parse(this.TextBox_Precio_Pactado.Text);
            string tipo = "";
            int confirmado_contraparte = 0;
            int confirmado_contrato = 0;
            int unwind = 0;
            string codigo_ins = "";
            string codigo_ra = "";

            if (this.radioButton_Fisico.IsChecked == true) {
                tipo = "F";
            }
            else if (this.radioButton_Compensacion.IsChecked == true)
            {
                tipo = "C";
            }

            if (this.checkBox_Confirmado_Contraparte.IsChecked == true)
            {
                confirmado_contraparte = 1;
            }

            if (this.checkBox_Confirmado_Contrato.IsChecked == true)
            {
                confirmado_contrato = 1;
            }

            if (this.checkBox_Unwind.IsChecked == true)
            {
                unwind = 1;
            }

            
            // Armamos el codigo de instrumento del forward
            codigo_ins = "FWD" + moneda_compra.Substring(0, 2) + moneda_venta.Substring(0, 2) + fecha_vcto.Month.ToString() + fecha_vcto.Day.ToString() + fecha_vcto.Year.ToString().Substring(2, 2);



            // Armamos el codigo de RiskAmerica del forward
            if (moneda_venta == "CLP" && moneda_compra == "USD")
            {
                codigo_ra = "FWC*P" + fecha_vcto.Day.ToString() + fecha_vcto.Month.ToString() + fecha_vcto.Year.ToString().Substring(2, 2);
            }
            else if (moneda_venta == "CLP" && moneda_compra == "EUR")
            {
                codigo_ra = "FWCRP" + fecha_vcto.Day.ToString() + fecha_vcto.Month.ToString() + fecha_vcto.Year.ToString().Substring(2, 2);
            }

            else if (moneda_compra == "CLP" && moneda_venta == "USD")
            {
                codigo_ra = "FWV*P" + fecha_vcto.Day.ToString() + fecha_vcto.Month.ToString() + fecha_vcto.Year.ToString().Substring(2, 2);
            }


            else if (moneda_compra == "CLP" && moneda_venta == "EUR")
            {
                codigo_ra = "FWVRP" + fecha_vcto.Day.ToString() + fecha_vcto.Month.ToString() + fecha_vcto.Year.ToString().Substring(2, 2);
            }


            //Subimos la tupla a la base de datos
            SqlConnection connection = LibreriaFdo.ConectDatabaseUser("Puyehue", "MesaInversiones", "usrConsultaComercial", "Comercial1w");
            string insert_statement = "INSERT INTO FWD_Monedas_Estatica (Fecha_Op, Codigo_Fdo, Codigo_Ins, Codigo_RA, Fecha_Fix, Fecha_Vcto, Codigo_Emi, Moneda_Compra, Moneda_Venta, Nominal_Compra, Nominal_Venta, Precio_Pactado, Tipo, Instrumento_Sintetico, Estrategia, Confirmado_Contraparte, Confirmado_Contrato, Unwind) VALUES (@Fecha_Op, @Codigo_Fdo, @Codigo_Ins, @Codigo_RA, @Fecha_Fix, @Fecha_Vcto, @Codigo_Emi, @Moneda_Compra, @Moneda_Venta, @Nominal_Compra, @Nominal_Venta, @Precio_Pactado, @Tipo, @Instrumento_Sintetico, @Estrategia, @Confirmado_Contraparte, @Confirmado_Contrato, @Unwind)";
            SqlCommand command = new SqlCommand(insert_statement);
            command.Connection = connection;
            command.Parameters.AddWithValue("@Fecha_Op", fecha_op);
            command.Parameters.AddWithValue("@Codigo_Fdo", codigo_fdo);
            command.Parameters.AddWithValue("@Codigo_Ins", codigo_ins);
            command.Parameters.AddWithValue("@Codigo_RA", codigo_ra);
            command.Parameters.AddWithValue("@Fecha_Fix", fecha_fix);
            command.Parameters.AddWithValue("@Fecha_Vcto", fecha_vcto);
            command.Parameters.AddWithValue("@Codigo_Emi", codigo_emi);
            command.Parameters.AddWithValue("@Moneda_Compra", moneda_compra);
            command.Parameters.AddWithValue("@Moneda_Venta", moneda_venta);
            command.Parameters.AddWithValue("@Nominal_Compra", nominal_compra);
            command.Parameters.AddWithValue("@Nominal_Venta", nominal_venta);
            command.Parameters.AddWithValue("@Precio_Pactado", precio_pactado);
            command.Parameters.AddWithValue("@Tipo", tipo);
            command.Parameters.AddWithValue("@Estrategia", estrategia);
            command.Parameters.AddWithValue("@Instrumento_Sintetico", instrumento_sintetico);
            command.Parameters.AddWithValue("@Confirmado_Contraparte", confirmado_contraparte);
            command.Parameters.AddWithValue("@Confirmado_Contrato", confirmado_contrato);
            command.Parameters.AddWithValue("@Unwind", unwind);
            try
            {
                int recordsAffected = command.ExecuteNonQuery();
                this.ComboBox_Codigo_Fdo.Text = "";
                this.ComboBox_Codigo_Emi.Text = "";
                this.ComboBox_Moneda_Compra.Text = "";
                this.ComboBox_Moneda_Venta.Text = "";
                this.ComboBox_Instrumento_Sintetico.Text = "";
                this.ComboBox_Estrategia.Text = "";
                this.TextBox_Nominal_Compra.Text = "";
                this.TextBox_Nominal_Venta.Text = "";
                this.TextBox_Precio_Pactado.Text = "";
                this.checkBox_Confirmado_Contraparte.IsChecked = false;
                this.checkBox_Confirmado_Contrato.IsChecked = false;
                this.checkBox_Unwind.IsChecked = false;
                MessageBox.Show("Instrumento agregado exitosamente.");
            }
            catch (Exception ex)
            {
                MessageBox.Show(ex.ToString());
            }
            LibreriaFdo.DisconnectDatabase(connection);
            this.Close();
        }
    }
}
