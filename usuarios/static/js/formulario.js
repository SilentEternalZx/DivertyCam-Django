const formulario=document.getElementById('form')

const inputs=document.querySelectorAll('#form input')


const expresiones={
    nombre: /^[a-zA-Z]{3,50}$/
}



const validarFormulario=(e)=>{
   switch(e.target.name){
    case "nombre":
        if(expresiones.nombre.test(e.target.value)){
           console.log("Bien")
        }else{
            document.getElementById('row').classList.add('row-error')
        }



    break;
 
    case "apellido":

    break;
    case "cedula":

    break;
    case "fechaNacimiento":

    break;
    case "direccion":

    break;
    case "telefono":

    break;
    case "usuario":

    break;
   }

}

inputs.forEach((input)=>{
    input.addEventListener('keyup', validarFormulario);
    input.addEventListener('blur', validarFormulario);
});

form.addEventListener('submit', ()=>{
    
  
})