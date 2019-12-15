async function deleteOutfit(element) {
    let body = {
        'outfit_id': element.getAttribute('data-id')
    };

    const response = await fetch('api/delete_outfit', {
        method: 'POST',
        body: JSON.stringify(body),
        headers: {
            'Content-Type': 'application/json'
        }
    });

    if (response.ok) {
        element.remove()
    }
}

for (let el of document.querySelectorAll('.outfit')) {
    el.addEventListener('click', evt => {
        if (evt.target.classList.contains('outfit-delete')) {
            deleteOutfit(el);
        }
    })
}
