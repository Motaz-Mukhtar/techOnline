#!/usr/bin/env node
let productForm = document.querySelector('form');


function postData(data, modelType) {
    fetch(`http://127.0.0.1:5001/api/v1/${modelType}`, data)
    .then(res => res.json())
    .then(data => console.log(data))
    .catch(err => console.error('Could not send'));
};

productForm.addEventListener('submit', (event) => {
    const postedData = {
        method: 'POST',
        body: new FormData(event.target)
    };

    postData(postedData, 'products');
});
