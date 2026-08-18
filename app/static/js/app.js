// This small object is enough for the list, selected contact, and form mode.
const state = {
  contacts: [],
  selectedId: null,
  savedContact: null,
  isNew: false,
};

const elements = {
  appShell: document.querySelector(".app-shell"),
  addContact: document.querySelector("#add-contact"),
  emptyAddContact: document.querySelector("#empty-add-contact"),
  backToContacts: document.querySelector("#back-to-contacts"),
  mobileContactTitle: document.querySelector("#mobile-contact-title"),
  search: document.querySelector("#contact-search"),
  list: document.querySelector("#contact-list"),
  listStatus: document.querySelector("#contact-list-status"),
  form: document.querySelector("#contact-form"),
  welcome: document.querySelector("#welcome-state"),
  firstName: document.querySelector("#first-name"),
  lastName: document.querySelector("#last-name"),
  company: document.querySelector("#company"),
  phone: document.querySelector("#phone"),
  birthday: document.querySelector("#birthday"),
  firstNameError: document.querySelector("#first-name-error"),
  lastNameError: document.querySelector("#last-name-error"),
  companyError: document.querySelector("#company-error"),
  phoneError: document.querySelector("#phone-error"),
  birthdayError: document.querySelector("#birthday-error"),
  formError: document.querySelector("#form-error"),
  toggleFavorite: document.querySelector("#toggle-favorite"),
  favoriteStar: document.querySelector("#toggle-favorite .favorite-star"),
  favoriteLabel: document.querySelector("#toggle-favorite .favorite-label"),
  emailList: document.querySelector("#email-list"),
  addEmail: document.querySelector("#add-email"),
  deleteContact: document.querySelector("#delete-contact"),
  cancelEdit: document.querySelector("#cancel-edit"),
  saveContact: document.querySelector("#save-contact"),
  deleteDialog: document.querySelector("#delete-dialog"),
  confirmDelete: document.querySelector("#confirm-delete"),
  toast: document.querySelector("#toast"),
  toastMessage: document.querySelector("#toast-message"),
  toastAction: document.querySelector("#toast-action"),
};

document.addEventListener("DOMContentLoaded", initialize);

async function initialize() {
  bindEvents();
  await loadContacts();
}

function bindEvents() {
  elements.addContact.addEventListener("click", startNewContact);
  elements.emptyAddContact.addEventListener("click", startNewContact);
  elements.backToContacts.addEventListener("click", returnToContactList);
  elements.search.addEventListener("input", renderContactList);
  elements.addEmail.addEventListener("click", () => addEmailField("", true));
  elements.form.addEventListener("submit", saveContact);
  elements.cancelEdit.addEventListener("click", cancelChanges);
  elements.toggleFavorite.addEventListener("click", toggleFavorite);
  elements.deleteContact.addEventListener("click", () => {
    elements.deleteDialog.showModal();
  });
  elements.confirmDelete.addEventListener("click", deleteContact);
}

async function loadContacts(preferredId = null) {
  showListStatus("Loading contacts...");

  try {
    state.contacts = await apiRequest("/api/contacts");
    renderContactList();

    if (state.contacts.length === 0) {
      showEmptyState();
      return;
    }

    const nextId = state.contacts.some((contact) => contact.id === preferredId)
      ? preferredId
      : state.contacts[0].id;
    await selectContact(nextId);
  } catch (error) {
    showListStatus("Contacts could not be loaded.");
    showFormError(error.message);
  }
}

function renderContactList() {
  const query = elements.search.value.trim().toLowerCase();
  const filteredContacts = state.contacts.filter((contact) => {
    const searchableText = [
      contact.first_name,
      contact.last_name,
      contact.company,
      contact.phone,
    ]
      .filter(Boolean)
      .join(" ")
      .toLowerCase();
    return searchableText.includes(query);
  });

  elements.list.replaceChildren();

  for (const contact of filteredContacts) {
    const listItem = document.createElement("li");
    const button = document.createElement("button");
    button.type = "button";
    const favoriteMarker = contact.is_favorite ? "★ " : "";
    // textContent displays user data without interpreting it as HTML.
    button.textContent = `${favoriteMarker}${contact.first_name} ${contact.last_name}`;
    button.dataset.contactId = contact.id;
    button.setAttribute("aria-current", String(contact.id === state.selectedId));
    button.addEventListener("click", () => selectContact(contact.id, true));
    listItem.append(button);
    elements.list.append(listItem);
  }

  if (state.contacts.length === 0) {
    showListStatus("No contacts yet.");
  } else if (filteredContacts.length === 0) {
    showListStatus("No matching contacts.");
  } else {
    elements.listStatus.hidden = true;
  }
}

async function selectContact(contactId, openDetails = false) {
  try {
    const contact = await apiRequest(`/api/contacts/${contactId}`);
    state.selectedId = contact.id;
    state.savedContact = contact;
    state.isNew = false;
    populateForm(contact);
    renderContactList();
    if (openDetails) showMobileDetails();
  } catch (error) {
    showToast(error.message);
  }
}

function startNewContact() {
  state.selectedId = null;
  state.savedContact = null;
  state.isNew = true;
  populateForm({
    first_name: "",
    last_name: "",
    company: "",
    phone: "",
    birthday: "",
    emails: [],
    is_favorite: false,
  });
  elements.deleteContact.hidden = true;
  showMobileDetails();
  elements.firstName.focus();
  renderContactList();
}

function populateForm(contact) {
  clearErrors();
  elements.welcome.hidden = true;
  elements.form.hidden = false;
  elements.firstName.value = contact.first_name;
  elements.lastName.value = contact.last_name;
  elements.company.value = contact.company || "";
  elements.phone.value = contact.phone || "";
  elements.birthday.value = contact.birthday || "";
  elements.mobileContactTitle.textContent = state.isNew
    ? "New contact"
    : `${contact.first_name} ${contact.last_name}`;
  elements.toggleFavorite.hidden = state.isNew;
  elements.toggleFavorite.setAttribute(
    "aria-pressed",
    String(Boolean(contact.is_favorite)),
  );
  elements.favoriteStar.textContent = contact.is_favorite ? "★" : "☆";
  elements.favoriteLabel.textContent = contact.is_favorite
    ? "Remove from favorites"
    : "Add to favorites";
  elements.emailList.replaceChildren();

  for (const email of contact.emails) {
    addEmailField(email);
  }

  elements.deleteContact.hidden = state.isNew;
}

function addEmailField(value = "", shouldFocus = false) {
  // Email rows are built with DOM methods so users can add any number of them.
  const row = document.createElement("div");
  row.className = "email-row";

  const inputWrap = document.createElement("div");
  inputWrap.className = "email-input-wrap";

  const input = document.createElement("input");
  input.type = "email";
  input.value = value;
  input.autocomplete = "email";
  input.placeholder = "name@example.com";
  input.setAttribute("aria-label", "Email address");

  const error = document.createElement("p");
  error.className = "email-error";

  const removeButton = document.createElement("button");
  removeButton.type = "button";
  removeButton.className = "remove-email";
  removeButton.setAttribute("aria-label", "Remove email address");
  removeButton.addEventListener("click", () => {
    row.remove();
  });

  inputWrap.append(input, error);
  row.append(inputWrap, removeButton);
  elements.emailList.append(row);

  if (shouldFocus) {
    input.focus();
  }
}

async function saveContact(event) {
  event.preventDefault();
  clearErrors();

  const payload = getFormData();
  const clientErrors = validateForm(payload);
  if (Object.keys(clientErrors).length > 0) {
    displayErrors(clientErrors);
    return;
  }

  const url = state.isNew ? "/api/contacts" : `/api/contacts/${state.selectedId}`;
  const method = state.isNew ? "POST" : "PUT";
  setSaving(true);

  try {
    const saved = await apiRequest(url, { method, body: JSON.stringify(payload) });
    showToast(state.isNew ? "Contact added." : "Changes saved.");
    await loadContacts(saved.id);
    showMobileDetails();
  } catch (error) {
    if (error.details) {
      displayErrors(error.details);
    } else {
      showFormError(error.message);
    }
  } finally {
    setSaving(false);
  }
}

function getFormData() {
  const emails = [...elements.emailList.querySelectorAll('input[type="email"]')]
    .map((input) => input.value.trim())
    .filter(Boolean);

  return {
    first_name: elements.firstName.value.trim(),
    last_name: elements.lastName.value.trim(),
    company: elements.company.value.trim(),
    phone: elements.phone.value.trim(),
    birthday: elements.birthday.value,
    emails,
  };
}

function validateForm(contact) {
  // Browser validation gives quick feedback; the API repeats it for data safety.
  const errors = {};

  if (!contact.first_name) errors.first_name = "First name is required.";
  if (!contact.last_name) errors.last_name = "Last name is required.";
  if (contact.company.length > 120) {
    errors.company = "Company must be 120 characters or fewer.";
  }
  if (contact.phone && !/^[0-9+().\-\s]{7,30}$/.test(contact.phone)) {
    errors.phone = "Enter a valid phone number.";
  }
  if (contact.birthday && contact.birthday > getLocalDate()) {
    errors.birthday = "Birthday cannot be in the future.";
  }

  const emailFields = {};
  const seen = new Set();
  contact.emails.forEach((email, index) => {
    const normalized = email.toLowerCase();
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(normalized)) {
      emailFields[index] = "Enter a valid email address.";
    } else if (seen.has(normalized)) {
      emailFields[index] = "This email is already listed.";
    }
    seen.add(normalized);
  });

  if (Object.keys(emailFields).length > 0) errors.email_fields = emailFields;
  return errors;
}

function displayErrors(errors) {
  if (errors.first_name) {
    elements.firstNameError.textContent = errors.first_name;
    elements.firstName.setAttribute("aria-invalid", "true");
  }
  if (errors.last_name) {
    elements.lastNameError.textContent = errors.last_name;
    elements.lastName.setAttribute("aria-invalid", "true");
  }
  if (errors.company) {
    elements.companyError.textContent = errors.company;
    elements.company.setAttribute("aria-invalid", "true");
  }
  if (errors.phone) {
    elements.phoneError.textContent = errors.phone;
    elements.phone.setAttribute("aria-invalid", "true");
  }
  if (errors.birthday) {
    elements.birthdayError.textContent = errors.birthday;
    elements.birthday.setAttribute("aria-invalid", "true");
  }
  if (errors.email_fields) {
    const rows = [...elements.emailList.querySelectorAll(".email-row")];
    for (const [index, message] of Object.entries(errors.email_fields)) {
      const row = rows[Number(index)];
      if (!row) continue;
      row.querySelector("input").setAttribute("aria-invalid", "true");
      row.querySelector(".email-error").textContent = message;
    }
  }
  if (errors.form || errors.emails) {
    showFormError(errors.form || errors.emails);
  }

  const firstInvalid = elements.form.querySelector('[aria-invalid="true"]');
  firstInvalid?.focus();
}

function clearErrors() {
  elements.firstNameError.textContent = "";
  elements.lastNameError.textContent = "";
  elements.companyError.textContent = "";
  elements.phoneError.textContent = "";
  elements.birthdayError.textContent = "";
  elements.firstName.removeAttribute("aria-invalid");
  elements.lastName.removeAttribute("aria-invalid");
  elements.company.removeAttribute("aria-invalid");
  elements.phone.removeAttribute("aria-invalid");
  elements.birthday.removeAttribute("aria-invalid");
  elements.formError.hidden = true;
  elements.formError.textContent = "";

  for (const input of elements.emailList.querySelectorAll("input")) {
    input.removeAttribute("aria-invalid");
  }
  for (const error of elements.emailList.querySelectorAll(".email-error")) {
    error.textContent = "";
  }
}

function cancelChanges() {
  if (state.isNew) {
    showMobileList();
    if (state.contacts.length > 0) {
      selectContact(state.contacts[0].id);
    } else {
      showEmptyState();
    }
    return;
  }

  populateForm(state.savedContact);
}

async function deleteContact(event) {
  event.preventDefault();
  elements.deleteDialog.close();
  const deletedId = state.selectedId;

  try {
    await apiRequest(`/api/contacts/${deletedId}`, { method: "DELETE" });
    state.selectedId = null;
    await loadContacts();
    showMobileList();
    // The action callback restores the same database row and all of its emails.
    showToast("Contact deleted.", {
      actionLabel: "Undo",
      duration: 7000,
      onAction: () => restoreContact(deletedId),
    });
  } catch (error) {
    showToast(error.message);
  }
}

async function restoreContact(contactId) {
  try {
    const restored = await apiRequest(`/api/contacts/${contactId}/restore`, {
      method: "POST",
    });
    await loadContacts(restored.id);
    showMobileDetails();
    showToast("Contact restored.");
  } catch (error) {
    showToast(error.message);
  }
}

async function toggleFavorite() {
  if (state.isNew || state.selectedId === null) return;

  const isFavorite = !state.savedContact.is_favorite;
  elements.toggleFavorite.disabled = true;

  try {
    const updated = await apiRequest(
      `/api/contacts/${state.selectedId}/favorite`,
      {
        method: "PATCH",
        body: JSON.stringify({ is_favorite: isFavorite }),
      },
    );
    await loadContacts(updated.id);
    showMobileDetails();
    showToast(
      isFavorite
        ? "Contact added to favorites."
        : "Contact removed from favorites.",
    );
  } catch (error) {
    showToast(error.message);
  } finally {
    elements.toggleFavorite.disabled = false;
  }
}

function returnToContactList() {
  showMobileList();
}

function showMobileDetails() {
  elements.appShell.classList.add("mobile-detail-open");
  window.scrollTo({ top: 0, behavior: "auto" });
}

function showMobileList() {
  elements.appShell.classList.remove("mobile-detail-open");
  window.scrollTo({ top: 0, behavior: "auto" });
}

function showEmptyState() {
  state.selectedId = null;
  state.savedContact = null;
  state.isNew = false;
  elements.form.hidden = true;
  elements.welcome.hidden = false;
  renderContactList();
}

function showListStatus(message) {
  elements.listStatus.textContent = message;
  elements.listStatus.hidden = false;
}

function getLocalDate() {
  const today = new Date();
  const year = today.getFullYear();
  const month = String(today.getMonth() + 1).padStart(2, "0");
  const day = String(today.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function showFormError(message) {
  elements.formError.textContent = message;
  elements.formError.hidden = false;
}

function setSaving(isSaving) {
  elements.saveContact.disabled = isSaving;
  elements.saveContact.textContent = isSaving ? "Saving..." : "Save";
}

let toastTimer;
function showToast(message, options = {}) {
  // The optional action turns the normal toast into the seven-second Undo prompt.
  window.clearTimeout(toastTimer);
  elements.toastMessage.textContent = message;
  elements.toastAction.hidden = !options.actionLabel;
  elements.toastAction.textContent = options.actionLabel || "";
  elements.toastAction.onclick = options.onAction
    ? () => {
        window.clearTimeout(toastTimer);
        elements.toast.hidden = true;
        options.onAction();
      }
    : null;
  elements.toast.hidden = false;
  toastTimer = window.setTimeout(() => {
    elements.toast.hidden = true;
    elements.toastAction.onclick = null;
  }, options.duration || 2600);
}

async function apiRequest(url, options = {}) {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  if (response.status === 204) return null;

  // fetch resolves for HTTP errors, so response.ok must be checked explicitly.
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    const error = new Error(body.error || "Something went wrong. Please try again.");
    error.details = body.errors;
    throw error;
  }

  return body;
}
