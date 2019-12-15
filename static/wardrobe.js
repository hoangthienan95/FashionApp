async function removeWardrobeItem(element) {
    let body = {
        'item_id': element.getAttribute('data-id')
    };

    const response = await fetch('api/remove_wardrobe_item', {
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

for (let el of document.querySelectorAll('.wardrobe-item')) {
    el.addEventListener('click', evt => {
        if (evt.target.classList.contains('wardrobe-remove')) {
            removeWardrobeItem(el);
        }
    })
}
