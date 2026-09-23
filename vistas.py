from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Form, Request
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError

from dependencias import ConnectionDep
from esquemas import ProductoActualizar
from repositorio import (
    actualizar_producto,
    obtener_producto,
    obtener_productos,
)


router = APIRouter(tags=["productos"])


# Buscar la carpeta templates desde la ubicación real
# de este archivo. Esto evita problemas al ejecutar
# la aplicación en Vercel.
BASE_DIR = Path(__file__).resolve().parent

templates = Jinja2Templates(
    directory=BASE_DIR / "templates"
)


# ---------------------------------------------------------
# LISTAR PRODUCTOS
# ---------------------------------------------------------

@router.get("/productos")
async def listar_productos(
    request: Request,
    conn: ConnectionDep,
):
    productos = await obtener_productos(conn)

    return templates.TemplateResponse(
        request=request,
        name="productos.html",
        context={
            "productos": productos,
        },
    )


# ---------------------------------------------------------
# EDITAR PRODUCTO
# ---------------------------------------------------------

@router.get("/productos/{producto_id}/editar")
async def editar_producto_vista(
    request: Request,
    conn: ConnectionDep,
    producto_id: int,
):
    producto = await obtener_producto(
        conn,
        producto_id,
    )

    # Si el producto no existe.
    if producto is None:
        return templates.TemplateResponse(
            request=request,
            name="componentes/producto_no_encontrado.html",
            context={
                "producto_id": producto_id,
            },
        )

    return templates.TemplateResponse(
        request=request,
        name="componentes/fila_editar.html",
        context={
            "producto": producto,
            "nombre": producto["nombre"],
            "precio": producto["precio"],
            "cantidad": producto["cantidad"],
            "descripcion": producto["descripcion"],
            "errores": {},
        },
    )


# ---------------------------------------------------------
# CANCELAR EDICIÓN
# ---------------------------------------------------------

@router.get("/productos/{producto_id}/cancelar")
async def cancelar_edicion_vista(
    request: Request,
    conn: ConnectionDep,
    producto_id: int,
):
    producto = await obtener_producto(
        conn,
        producto_id,
    )

    if producto is None:
        return templates.TemplateResponse(
            request=request,
            name="componentes/producto_no_encontrado.html",
            context={
                "producto_id": producto_id,
            },
        )

    return templates.TemplateResponse(
        request=request,
        name="componentes/fila_producto.html",
        context={
            "producto": producto,
        },
    )


# ---------------------------------------------------------
# GUARDAR PRODUCTO
# ---------------------------------------------------------

@router.post("/productos/{producto_id}")
async def guardar_producto_vista(
    request: Request,
    conn: ConnectionDep,
    producto_id: int,

    nombre: Annotated[
        str | None,
        Form()
    ] = None,

    precio: Annotated[
        str | None,
        Form()
    ] = None,

    cantidad: Annotated[
        str | None,
        Form()
    ] = None,

    descripcion: Annotated[
        str | None,
        Form()
    ] = None,
):

    # -----------------------------------------------------
    # Convertir precio y cantidad
    # -----------------------------------------------------

    try:

        precio_numero = (
            float(precio)
            if precio is not None
            else None
        )

        cantidad_numero = (
            int(cantidad)
            if cantidad is not None
            else None
        )

        datos = ProductoActualizar(
            nombre=nombre,
            precio=precio_numero,
            cantidad=cantidad_numero,
            descripcion=descripcion,
        )

    # -----------------------------------------------------
    # Error al convertir números
    # -----------------------------------------------------

    except ValueError:

        producto = await obtener_producto(
            conn,
            producto_id,
        )

        if producto is None:
            return templates.TemplateResponse(
                request=request,
                name="componentes/producto_no_encontrado.html",
                context={
                    "producto_id": producto_id,
                },
            )

        errores = {}

        # Comprobar únicamente qué campo falló.
        if precio is not None:

            try:
                float(precio)

            except ValueError:
                errores["precio"] = (
                    "El precio debe ser un número válido."
                )

        if cantidad is not None:

            try:
                int(cantidad)

            except ValueError:
                errores["cantidad"] = (
                    "La cantidad debe ser un número entero válido."
                )

        return templates.TemplateResponse(
            request=request,
            name="componentes/fila_editar.html",
            context={
                "producto": producto,
                "nombre": nombre,
                "precio": precio,
                "cantidad": cantidad,
                "descripcion": descripcion,
                "errores": errores,
            },
            status_code=422,
        )

    # -----------------------------------------------------
    # Errores de validación de Pydantic
    # -----------------------------------------------------

    except ValidationError as error:

        producto = await obtener_producto(
            conn,
            producto_id,
        )

        if producto is None:
            return templates.TemplateResponse(
                request=request,
                name="componentes/producto_no_encontrado.html",
                context={
                    "producto_id": producto_id,
                },
            )

        errores = {}

        for detalle in error.errors():

            campo = detalle["loc"][0]

            errores[campo] = detalle["msg"]

        return templates.TemplateResponse(
            request=request,
            name="componentes/fila_editar.html",
            context={
                "producto": producto,
                "nombre": nombre,
                "precio": precio,
                "cantidad": cantidad,
                "descripcion": descripcion,
                "errores": errores,
            },
            status_code=422,
        )

    # -----------------------------------------------------
    # Actualizar producto
    # -----------------------------------------------------

    actualizado = await actualizar_producto(
        conn,
        producto_id,
        datos.nombre,
        datos.precio,
        datos.cantidad,
        datos.descripcion,
    )

    # Si no se pudo actualizar porque no existe.
    if not actualizado:

        return templates.TemplateResponse(
            request=request,
            name="componentes/producto_no_encontrado.html",
            context={
                "producto_id": producto_id,
            },
        )

    # Obtener nuevamente el producto actualizado.
    producto = await obtener_producto(
        conn,
        producto_id,
    )

    return templates.TemplateResponse(
        request=request,
        name="componentes/fila_actualizada.html",
        context={
            "producto": producto,
        },
    )