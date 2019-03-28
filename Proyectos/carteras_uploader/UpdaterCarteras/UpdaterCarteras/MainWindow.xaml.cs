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
using System.Windows.Navigation;
using System.Windows.Shapes;

namespace UpdaterCarteras
{
    /// <summary>
    /// Lógica de interacción para MainWindow.xaml
    /// </summary>
    public partial class MainWindow : Window
    {
        public MainWindow()
        {
            InitializeComponent();
        }

        private void Boton_Emisores_Click(object sender, RoutedEventArgs e)
        {
            this.Hide();
            EmisorWindow emisor_window = new EmisorWindow(this);
            emisor_window.Show();
        }

        private void Boton_Instrumentos_Click(object sender, RoutedEventArgs e)
        {
            this.Hide();
            InstrumentoWindow instrumento_window = new InstrumentoWindow(this);
            instrumento_window.Show();
        }

        private void Boton_FXForward_Click(object sender, RoutedEventArgs e)
        {
            this.Hide();
            FXForwardWindow fxforward_window = new FXForwardWindow(this);
            fxforward_window.Show();
        }

        private void Boton_Estrategias_Click(object sender, RoutedEventArgs e)
        {
            this.Hide();
            EstrategiaWindow estrategia_window = new EstrategiaWindow(this);
            estrategia_window.Show();
        }

        private void Boton_Indices_Click(object sender, RoutedEventArgs e)
        {
            this.Hide();
            IndiceWindow indice_window = new IndiceWindow(this);
            indice_window.Show();
        }
    }
}
