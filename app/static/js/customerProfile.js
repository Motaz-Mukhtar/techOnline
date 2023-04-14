#!/usr/bin/env node

let profileForm = document.querySelector(".profile_form"),
    editButton = document.querySelector(".edit_button"),
    submitButton = document.querySelector(".submit_button");

console.log(profileForm)
console.log(editButton)
console.log(submitButton)


function postData(data, modelType) {
    fetch(`http://127.0.0.1:5001/api/v1/${modelType}`, data)
    .then(res => res.json())
    .then(data => console.log(data))
    .catch(err => console.error('Could not send'));
};

function editData() {
    for (let i = 0; i < profileForm.elements.length - 1; i++){
        profileForm[i].attributes.removeNamedItem('disabled')
    }
    submitButton.style.display = 'block';
    document.querySelector('.cancel_button').style.display = 'block';
}

profileForm.addEventListener('submit', (event) => {
    const postedData = {
        method: 'PUT',
        body: new FormData(event.target)
    };

    postData(postedData, `customers/${profileForm.attributes['data-id'].value}`);
});


editButton.addEventListener('click', () => editData())

