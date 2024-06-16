const textTranslations = [
    
];

const titleTranslations = {
    "Remote Power Control": "Remote Power Control",
};

const placeholdersTranslations = {};

const alternativeTextTranslations = {};

const elementsTitlesTranslations = {};

const dataBSTranslations = {};

if (window.navigator.language.split("-")[0] == "pl") {
    document.querySelector("html").lang = "pl";
    // document.querySelector("link[rel=manifest]").href = "/manifest_pl.json";
    document.querySelector("title").innerHTML = titleTranslations[document.querySelector("title").innerHTML];
    document.querySelectorAll("[text-id]").forEach((e) => { e.innerHTML = textTranslations[e.getAttribute("text-id")]; });
    document.querySelectorAll("[placeholder]").forEach((e) => { e.placeholder = placeholdersTranslations[e.placeholder]; });
    document.querySelectorAll("[alt]").forEach((e) => { e.alt = alternativeTextTranslations[e.alt]; });
    document.querySelectorAll("[title]").forEach((e) => { e.title = elementsTitlesTranslations[e.title]; });
    document.querySelectorAll("[data-bs-original-title]").forEach((e) => { e.setAttribute("data-bs-original-title", dataBSTranslations[e.getAttribute("data-bs-original-title")] ); });
}
