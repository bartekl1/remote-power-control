const textTranslations = [
    "Zaloguj się",
    "Nazwa użytkownika",
    "Hasło",
    "Zaloguj się z",
    "Zła nazwa użytkownika lub hasło",
    "Wystąpił błąd",
    "Błędne TOTP",
    "Anuluj",
    "Edytuj użytkownika",
    "Zmień hasło",
    "Wyloguj się",
    "Nazwa użytkownika jest zajęta",
    "E-mail jest używany do pobierania zdjęcia profilowego z",
    "Zapisz",
    "Hasła nie są takie same",
    "Powtórz hasło",
    "Włącz",
    "Wyłącz",
    "2FA jest włączone",
    "2FA jest wyłączone",
    "Dodaj",
    "Dodaj urządzenie",
    "Nazwa",
    "Adres MAC",
    "Adres IP",
    "Nazwa użytkownika SSH",
    "Typ klucza SSH",
    "Klucz SSH",
    "Hasło SSH",
    "Polecenie zamykania",
    "Polecenie restartu",
    "Polecenie wylogowywania",
    "Polecenie uśpienia",
    "Polecenie hibernacji",
];

const titleTranslations = {
    "Remote Power Control": "Remote Power Control",
    "Log in": "Zaloguj się",
};

const placeholdersTranslations = {};

const alternativeTextTranslations = {};

const elementsTitlesTranslations = {};

const dataBSTranslations = {
    "Edit": "Edytuj",
    "Delete": "Usuń",
    "Wake up": "Obudź",
    "Shut down": "Zamknij",
    "Reboot": "Uruchom ponownie",
    "Log out": "Wyloguj",
    "Sleep": "Uśpij",
    "Hibernate": "Hibernuj",
    "Add": "Dodaj",
};

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
