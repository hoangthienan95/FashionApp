let outfitCategoryElements = {};
let recommendCategoryElements = {};

let categories = [];
let outfitCategoryItems = {};
let recommendCategoryItems = {};

for (let el of document.querySelectorAll('#outfit > .category')) {
    const cat = el.getAttribute('data-category');
    categories.push(cat);
    outfitCategoryElements[cat] = el;
    outfitCategoryItems[cat] = [];
}

for (let el of document.querySelectorAll('#recommend > .category')) {
    const cat = el.getAttribute('data-category');
    recommendCategoryElements[cat] = el;
    recommendCategoryItems[cat] = [];
}

function createImg(itemId, itemPath, itemCategory, inWardrobe) {
    const imgEl = document.createElement('img');
    imgEl.setAttribute('data-id', itemId);
    imgEl.setAttribute('data-category', itemCategory);
    imgEl.src = itemPath;
    imgEl.classList.add('creator-item');
    if (!inWardrobe) {
        imgEl.classList.add('not-in-wardrobe');
    }

    return imgEl
}

function addItem(itemId, itemPath, itemCategory, inWardrobe, itemDict, elementDict) {
    const catList = itemDict[itemCategory];
    if (catList.includes(itemId)) {
        return false;
    }

    catList.push(itemId);

    const imgEl = createImg(itemId, itemPath, itemCategory, inWardrobe);
    elementDict[itemCategory].appendChild(imgEl);
    return true
}

function addOutfitItem(element) {
    const itemId = element.getAttribute('data-id');
    const itemPath = element.getAttribute('src');
    const itemCategory = element.getAttribute('data-category');
    const inWardrobe = element.classList.contains('in-wardrobe');

    if (addItem(itemId, itemPath, itemCategory, inWardrobe, outfitCategoryItems, outfitCategoryElements)) {
        loadRecommendations(itemId);
    }
}

function removeOutfitItem(element) {
    const imgPath = element.getAttribute('src');
    const imgId = element.getAttribute('data-id');
    const imgCat = element.getAttribute('data-category');

    const catList = outfitCategoryItems[imgCat];

    if (catList.includes(imgId)) {
        catList.splice(catList.indexOf(imgId), 1);

        element.remove();
    }
}

document.getElementById('wardrobe').addEventListener('click', ev => {
    if (ev.target.classList.contains('creator-item')) {
        addOutfitItem(ev.target);
    }
});

document.getElementById('outfit').addEventListener('click', ev => {
    if (ev.target.classList.contains('creator-item')) {
        removeOutfitItem(ev.target);
    }
});

document.getElementById('recommend').addEventListener('click', ev => {
    if (ev.target.classList.contains('creator-item')) {
        addOutfitItem(ev.target);
    }
});

function addRecommendationItem(itemId, itemPath, itemCategory, inWardrobe) {
    addItem(itemId, itemPath, itemCategory, inWardrobe, recommendCategoryItems, recommendCategoryElements);
}

async function loadRecommendations(itemId) {
    const body = {
        'item_id': itemId,
        'wardrobe': 'random'
    };

    const response = await fetch('api/recommend', {
        method: 'POST',
        body: JSON.stringify(body),
        headers: {
            'Content-Type': 'application/json'
        }
    });

    if (response.ok) {
        const responseJson = await response.json();
        console.log(responseJson);

        for (let item of responseJson['results']) {
            addRecommendationItem(item['id'], item['path'], item['category'], item['in_wardrobe']);
        }
    }
}

async function submitOutfit() {
    let body = {
        'items': []
    };

    for (let cat of categories) {
        for (let itemId of outfitCategoryItems[cat]) {
            body['items'].push(itemId)
        }
    }

    const name = document.getElementById('outfit-name').value;

    if (name !== '') {
        body['name'] = name;
    }

    const response = await fetch('api/create_outfit', {
        method: 'POST',
        body: JSON.stringify(body),
        headers: {
            'Content-Type': 'application/json'
        }
    });

    if (response.ok) {
        window.location = '/outfits'
    }
}

document.getElementById('create-button').addEventListener('click', ev => {
    submitOutfit();
});
