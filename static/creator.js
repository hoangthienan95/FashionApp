let categoryElements = {};
let categories = [];
let categoryItems = {};

for (let el of document.querySelectorAll('.outfit-category')) {
    const cat = el.getAttribute('data-category');
    categories.push(cat);
    categoryElements[cat] = el;
    categoryItems[cat] = [];
}

function addOutfitItem(element) {
    const imgPath = element.getAttribute('src');
    const imgId = element.getAttribute('data-id');
    const imgCat = element.getAttribute('data-category');

    const catList = categoryItems[imgCat];
    if (!catList.includes(imgId)) {
        catList.push(imgId);

       const imgEl = document.createElement('img');
       imgEl.setAttribute('data-id', imgId);
       imgEl.setAttribute('data-category', imgCat);
       imgEl.src = imgPath;
       imgEl.classList.add('creator-item-lg');

       categoryElements[imgCat].appendChild(imgEl);
    }
}

function removeOutfitItem(element) {
    const imgPath = element.getAttribute('src');
    const imgId = element.getAttribute('data-id');
    const imgCat = element.getAttribute('data-category');

    const catList = categoryItems[imgCat];

    if (catList.includes(imgId)) {
        catList.splice(catList.indexOf(imgId), 1);

        element.remove();
    }
    console.log(categoryItems);
}

document.getElementById('wardrobe').addEventListener('click', ev => {
    if (ev.target.classList.contains('creator-item-sm')) {
        addOutfitItem(ev.target);
    }
});

document.getElementById('outfit').addEventListener('click', ev => {
    if (ev.target.classList.contains('creator-item-lg')) {
        removeOutfitItem(ev.target);
    }
});
