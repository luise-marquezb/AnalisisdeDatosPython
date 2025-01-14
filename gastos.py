import streamlit as st
import json
from datetime import datetime
import pandas as pd
import plotly.express as px

# --- Funciones de manejo de datos ---
def load_data():
    try:
        with open('data.json', 'r') as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = {"ingresos": [], "egresos": [], "usuarios": []}
    return data

def save_data(data):
    with open('data.json', 'w') as f:
        json.dump(data, f, indent=4)

# --- Funciones de visualización ---
def display_dashboard(data):
    st.header("Dashboard de Ingresos y Egresos")

    # El filtro de mes ya no es seleccionable
    mes_seleccionado = 'Todos'


    # --- Calcula totales
    total_ingresos = sum(item['importe'] for item in data['ingresos'])
    total_egresos = sum(item['importe'] for item in data['egresos'])
    saldo = total_ingresos - total_egresos

    st.write(f"Total Ingresos: {total_ingresos:.2f}")
    st.write(f"Total Egresos: {total_egresos:.2f}")
    st.write(f"Saldo Actual: {saldo:.2f}")

    # --- Preparación de datos para el gráfico
    if data['ingresos'] or data['egresos']:
        df_ingresos = pd.DataFrame(data['ingresos'])
        df_egresos = pd.DataFrame(data['egresos'])

        # Verificar la existencia de la columna fecha y aplicar el formato correcto
        if not df_ingresos.empty:
            df_ingresos['mes_año'] = df_ingresos['fecha'].apply(lambda x: datetime.strptime(x, '%Y-%m-%d').strftime('%Y-%m'))
        
        if not df_egresos.empty:
            df_egresos['mes_año'] = df_egresos['fecha'].apply(lambda x: datetime.strptime(x, '%Y-%m-%d').strftime('%Y-%m'))

        # Agrupar por mes y calcular totales
        if not df_ingresos.empty:
            ingresos_mensuales = df_ingresos.groupby('mes_año')['importe'].sum().reset_index()
        else:
           ingresos_mensuales = pd.DataFrame(columns = ['mes_año', 'importe'])
        if not df_egresos.empty:
           egresos_mensuales = df_egresos.groupby('mes_año')['importe'].sum().reset_index()
        else:
          egresos_mensuales = pd.DataFrame(columns = ['mes_año', 'importe'])
        
        # Unir en un solo df
        df_unido = pd.merge(ingresos_mensuales, egresos_mensuales, on='mes_año', suffixes=('_ingresos', '_egresos'), how='outer').fillna(0)

        # Transformar el dataframe para el grafico agrupado
        df_unido_melted = pd.melt(df_unido, id_vars=['mes_año'], value_vars=['importe_ingresos','importe_egresos'],
                                    var_name = 'tipo', value_name = 'importe')
        
        df_unido_melted['tipo'] = df_unido_melted['tipo'].replace({'importe_ingresos':'Ingresos', 'importe_egresos':'Egresos'})
        
        # Crear el gráfico de barras agrupadas
        fig = px.bar(df_unido_melted, x='mes_año', y='importe', color='tipo',
                     title='Ingresos vs Egresos Mensuales',
                     labels={'importe': 'Importe', 'mes_año': 'Mes'},
                     barmode='group')
        st.plotly_chart(fig)

    else:
      st.write("No hay datos para mostrar en el gráfico")



def display_consultar_ingresos(data):
    st.header("Consultar Ingresos por Usuario y Mes")
    mes_consulta = st.selectbox("Seleccione el mes a consultar", ['Todos'] + sorted(set([item['fecha'].split('-')[1] for item in data['ingresos']])))
    usuario_consulta = st.selectbox("Seleccione el usuario a consultar", ['Todos'] + sorted(set([item['nombre'] for item in data['ingresos']])))

    filtered_ingresos = data['ingresos']

    if mes_consulta != 'Todos':
        filtered_ingresos = [ingreso for ingreso in filtered_ingresos if ingreso['fecha'].split('-')[1] == mes_consulta]

    if usuario_consulta != 'Todos':
        filtered_ingresos = [ingreso for ingreso in filtered_ingresos if ingreso['nombre'] == usuario_consulta]

    if filtered_ingresos:
        df_filtered_ingresos = pd.DataFrame(filtered_ingresos)
        st.dataframe(df_filtered_ingresos)
    else:
        st.write("No se encontraron ingresos para los filtros seleccionados.")

# --- Funciones de formularios ---
def input_ingresos(data):
    st.header("Registro de Ingresos")
    nombre = st.text_input("Nombre de quien hace el ingreso")
    fecha_ingreso = st.date_input("Fecha del Ingreso")
    metodo_pago = st.selectbox("Método de Pago", ["Yape", "Plin", "Efectivo", "Transferencia", "Otro"])
    importe = st.number_input("Importe del Ingreso", min_value=0.0)

    if st.button("Registrar Ingreso"):
        data['ingresos'].append({
            'nombre': nombre,
            'fecha': fecha_ingreso.strftime('%Y-%m-%d'),
            'metodo': metodo_pago,
            'importe': importe
        })
        save_data(data)
        st.success("Ingreso registrado correctamente.")

def input_egresos(data):
    st.header("Registro de Egresos")
    descripcion = st.text_input("Descripción del Gasto")
    fecha_gasto = st.date_input("Fecha del Gasto")
    metodo_pago = st.selectbox("Método de Pago", ["Efectivo", "Tarjeta", "Transferencia", "Otro"])
    mes_pago = st.selectbox("Mes del Gasto", ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"])
    importe = st.number_input("Importe del Gasto", min_value=0.0)

    if st.button("Registrar Egreso"):
        data['egresos'].append({
            'fecha': fecha_gasto.strftime('%Y-%m-%d'),
            'descripcion': descripcion,
            'metodo': metodo_pago,
            'mes': mes_pago,
            'importe': importe
        })
        save_data(data)
        st.success("Egreso registrado correctamente.")

# --- Funciones para editar y eliminar datos ---
def manage_data(data, type):
    st.header(f"Gestionar {type.capitalize()}")

    if type == 'ingresos':
       items = data['ingresos']
       if items:
          df = pd.DataFrame(items)
          st.dataframe(df)

          st.subheader("Filtrar Ingresos")
          col1, col2 = st.columns(2)

          with col1:
            mes_filter = st.selectbox("Filtrar por Mes", ['Todos'] + sorted(set([item['fecha'].split('-')[1] for item in items])))
          with col2:
            user_filter = st.selectbox("Filtrar por Usuario", ['Todos'] + sorted(set([item['nombre'] for item in items])))

          filtered_items = items
          if mes_filter != "Todos":
            filtered_items = [item for item in filtered_items if item['fecha'].split('-')[1] == mes_filter]
          if user_filter != "Todos":
            filtered_items = [item for item in filtered_items if item['nombre'] == user_filter]

          if filtered_items:
            st.subheader(f"Editar o Eliminar {type[:-1]}")
            selected_item_index = st.selectbox(f"Selecciona el {type[:-1]} a modificar o eliminar:", range(len(filtered_items)), format_func = lambda x: f"{filtered_items[x]['nombre']} - {filtered_items[x]['fecha']} - {filtered_items[x]['importe']}")
            selected_item = filtered_items[selected_item_index]

            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"Modificar {type[:-1]}"):
                    nombre = st.text_input("Nombre:", value = selected_item['nombre'])
                    fecha = st.date_input("Fecha:", value=datetime.strptime(selected_item['fecha'], '%Y-%m-%d').date() if selected_item['fecha'] else None)
                    importe = st.number_input("Importe:", value=selected_item['importe'])
                    metodo_pago = st.selectbox("Método de Pago", ["Yape", "Plin", "Efectivo", "Transferencia", "Otro"], index = ["Yape", "Plin", "Efectivo", "Transferencia", "Otro"].index(selected_item['metodo']))

                    if st.button("Guardar cambios"):
                        index = data['ingresos'].index(selected_item)
                        data['ingresos'][index] = {'nombre': nombre,
                          'fecha': fecha.strftime('%Y-%m-%d'),
                          'importe': importe,
                           'metodo': metodo_pago,
                           }
                        save_data(data)
                        st.success(f"{type[:-1]} modificado correctamente")
            with col2:
                if st.button(f"Eliminar {type[:-1]}"):
                    index = data['ingresos'].index(selected_item)
                    del data['ingresos'][index]
                    save_data(data)
                    st.success(f"{type[:-1]} eliminado correctamente")
          else:
              st.write(f"No se encontraron {type} con los filtros seleccionados.")
       else:
         st.write(f"No hay {type} registrados.")


    elif type == 'egresos':
        items = data['egresos']
        if items:
            df = pd.DataFrame(items)
            st.dataframe(df)
            st.subheader("Filtrar Egresos")
            mes_filter = st.selectbox("Filtrar por Mes", ['Todos'] + sorted(set([item['mes'] for item in items])))

            filtered_items = items
            if mes_filter != "Todos":
                filtered_items = [item for item in filtered_items if item['mes'] == mes_filter]

            if filtered_items:
                st.subheader(f"Editar o Eliminar {type[:-1]}")
                selected_item_index = st.selectbox(f"Selecciona el {type[:-1]} a modificar o eliminar:", range(len(filtered_items)), format_func = lambda x: f"{filtered_items[x]['descripcion']} - {filtered_items[x]['fecha']} - {filtered_items[x]['importe']}")
                selected_item = filtered_items[selected_item_index]

                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"Modificar {type[:-1]}"):
                        descripcion = st.text_input("Descripción del Gasto", value= selected_item['descripcion'])
                        fecha = st.date_input("Fecha del Gasto", value=datetime.strptime(selected_item['fecha'], '%Y-%m-%d').date() if selected_item['fecha'] else None)
                        metodo_pago = st.selectbox("Método de Pago", ["Efectivo", "Tarjeta", "Transferencia", "Otro"], index = ["Efectivo", "Tarjeta", "Transferencia", "Otro"].index(selected_item['metodo']))
                        mes_pago = st.selectbox("Mes del Gasto", ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"], index = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"].index(selected_item['mes']) )
                        importe = st.number_input("Importe del Gasto", min_value=0.0, value = selected_item['importe'])

                        if st.button("Guardar cambios"):
                            index = data['egresos'].index(selected_item)
                            data['egresos'][index] = {
                                'fecha': fecha.strftime('%Y-%m-%d'),
                                'descripcion': descripcion,
                                'metodo': metodo_pago,
                                'mes': mes_pago,
                                'importe': importe
                            }
                            save_data(data)
                            st.success(f"{type[:-1]} modificado correctamente")
                with col2:
                    if st.button(f"Eliminar {type[:-1]}"):
                       index = data['egresos'].index(selected_item)
                       del data['egresos'][index]
                       save_data(data)
                       st.success(f"{type[:-1]} eliminado correctamente")
            else:
               st.write(f"No se encontraron {type} con los filtros seleccionados.")
        else:
            st.write(f"No hay {type} registrados.")

# --- Interfaz de Streamlit ---
def main():
    st.title("Control de Ingresos y Egresos")
    data = load_data()

    menu = st.sidebar.selectbox("Menú", ["Dashboard", "Registro de Ingresos", "Registro de Egresos", "Consultar Ingresos", "Gestionar Ingresos", "Gestionar Egresos"])

    if menu == "Dashboard":
        display_dashboard(data)
    elif menu == "Registro de Ingresos":
        input_ingresos(data)
    elif menu == "Registro de Egresos":
        input_egresos(data)
    elif menu == "Consultar Ingresos":
        display_consultar_ingresos(data)
    elif menu == "Gestionar Ingresos":
        manage_data(data, "ingresos")
    elif menu == "Gestionar Egresos":
        manage_data(data, "egresos")

if __name__ == '__main__':
    main()
