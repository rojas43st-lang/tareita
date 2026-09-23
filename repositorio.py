# Este archivo concentra las consultas SQL.

# Todas las consultas utilizan parámetros ($1, $2, etc.)
# para evitar concatenar directamente los valores recibidos
# desde el formulario.


async def obtener_productos(conn) -> list[dict]:
    filas = await conn.fetch(
        """
        SELECT
            id,
            nombre,
            precio,
            cantidad,
            descripcion
        FROM productos
        ORDER BY nombre
        """
    )

    return [dict(fila) for fila in filas]


async def obtener_producto(
    conn,
    producto_id: int,
) -> dict | None:

    fila = await conn.fetchrow(
        """
        SELECT
            id,
            nombre,
            precio,
            cantidad,
            descripcion
        FROM productos
        WHERE id = $1
        """,
        producto_id,
    )

    if fila is None:
        return None

    return dict(fila)


async def actualizar_producto(
    conn,
    producto_id: int,
    nombre: str,
    precio: float,
    cantidad: int,
    descripcion: str | None,
) -> bool:

    resultado = await conn.execute(
        """
        UPDATE productos
        SET
            nombre = $1,
            precio = $2,
            cantidad = $3,
            descripcion = $4
        WHERE id = $5
        """,
        nombre,
        precio,
        cantidad,
        descripcion,
        producto_id,
    )

    return resultado == "UPDATE 1"