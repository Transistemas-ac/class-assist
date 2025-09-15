# class-assist 🧮

Script que genera una tabla basado en una lista de alumnxs y logs de zoom o resultados de formulario de asistencia

<br>

## Cómo funciona

El funcionamiento actual es el siguiente:

1. Se toman los archivos de logs y resultados de formulario ubicados en una carpeta input
2. Se limpian los datos de ambos tipos de archivos removiendo datos innecesarios y juntando otros
3. Se combinan los tipos de archivo (log y form) en un solo DataFrame para cada tipo
4. Luego se cargan los datos de cada alumnx de un archivo alumni.csv incorporado en la carpeta data
5. Con todos los datos, se extraen las fechas únicas existentes en los DataFrames combinados del paso 3
6. Se genera un map para cada alumnx en la lista con su nombre, nombre alternativo y su email
7. Se checkea para cada fecha si el identificador de cada alumnx está presente en el DataFrame de logs o forms y se determina su status: both (ambos), log, form, absent (ausente)
8. La tabla creada a partir del paso 4 se convierte en un nuevo DataFrame, se organiza y exporta

<br>

## Siguientes pasos a implementar

Lo que está presente en esta primera carga es solo una especie de demo, hay un número de items que querría implementar luego de conversarlos y llegar a acuerdos en cuanto a nombres y algunos pasos manuales

- Agregar un input adicional relacionado a un form de ausencia, con el fin de que quienes se ausenten puedan completar un form estático que esté siempre abierto o mismo una tabla donde profes puedan cargar ausencias justificadas y se pueda procesar en el script
- Conectar a drive
  - El primer objetivo es poder descargar automáticamente los archivos que se vayan subiendo
  - El segundo paso sería poder subir a una carpeta el reporte final, con un nombre más apropiado, e implementar la lógica de sobreescribir o crear archivo si no existiese
- Procesar los nombres originales de cada archivo
  - En esta demo apliqué modificaciones manuales para renombrar los archivos, porque no sabía si habían sido actualizados de manera manual anteriormente o no, por lo que poder convertir de nombre base a un nombre más ordenado sería útil
- Definir mejores palabras o las más apropiadas para utilizar, dado que usé muchos placeholders y comentarios en inglés por costumbre
- Definir cuándo y cómo correr el script, de manera manual, automática, tiempo después de la clase, etc
