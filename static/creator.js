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

function createImg(itemId, itemPath, itemCategory) {
    const imgEl = document.createElement('img');
    imgEl.setAttribute('data-id', itemId);
    imgEl.setAttribute('data-category', itemCategory);
    imgEl.src = itemPath;
    imgEl.classList.add('creator-item');

    return imgEl
}

function addItem(itemId, itemPath, itemCategory, itemDict, elementDict) {
    const catList = itemDict[itemCategory];
    if (catList.includes(itemId)) {
        return false;
    }

    catList.push(itemId);

    const imgEl = createImg(itemId, itemPath, itemCategory);
    elementDict[itemCategory].appendChild(imgEl);
    return true
}

function addOutfitItem(element) {
    const itemId = element.getAttribute('data-id');
    const itemPath = element.getAttribute('src');
    const itemCategory = element.getAttribute('data-category');

    if (addItem(itemId, itemPath, itemCategory, outfitCategoryItems, outfitCategoryElements)) {
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
    console.log(outfitCategoryItems);
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

function addRecommendationItem(itemId, itemPath, itemCategory) {
    addItem(itemId, itemPath, itemCategory, recommendCategoryItems, recommendCategoryElements);
}

async function loadRecommendations(itemId) {
    const body = {
        'item_id': itemId,
        'wardrobe': false
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
            addRecommendationItem(item['id'], item['path'], item['category'])
        }
    }
}
