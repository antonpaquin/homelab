function clearChildren(target) {
    while (target.children.length) {
        target.removeChild(target.children[0]);
    }
}

class App {
    constructor() {
        this.lakeview = new LakeView(this);
        this.libraryview = new LibraryView(this);
    }

    render(id) {
        let target = document.getElementById(id);
        clearChildren(target);

        this.lakeview.render(target);
        this.libraryview.render(target);
    }

    selectFile(treeFile) {
        this.libraryview.addFile(treeFile);
        treeFile.hide();
    }

    unselectFile(treeFile) {
        this.libraryview.removeFile(treeFile);
        treeFile.show();
    }
}

class LakeView {
    constructor(app) {
        this.app = app;

        this.root = document.createElement("div");
        this.root.classList.add("tree-main");

        this.tree = null;

        this.req();
    }

    render(parent) {
        parent.appendChild(this.root);
    }

    req() {
        let xhr = new XMLHttpRequest();
        xhr.addEventListener("load", () => {
            this.load(JSON.parse(xhr.response));
        });
        xhr.open("GET", "/tree");
        xhr.send();
    }

    load(response) {
        this.tree = new TreeDir(this.app, response, "");
        this.tree.render(this.root);
    }
}

class TreeDir {
    constructor(app, spec, prefix) {
        this.app = app;
        this.spec = spec;

        this.root = document.createElement("div");
        this.root.classList.add("tree-dir");
        this.root.classList.add("collapsed");

        this.name = document.createElement("span");
        this.name.classList.add("tree-dir-label")
        this.name.innerText = spec.name;
        this.name.onclick = (ev) => {this.toggleCollapse()};

        let nprefix = prefix + spec.name + "/";

        this.dirs = [];
        for (let dir of spec.dirs) {
            this.dirs.push(new TreeDir(app, dir, nprefix));
        }

        this.files = [];
        for (let file of spec.files) {
            this.files.push(new TreeFile(app, file, nprefix));
        }

        this.root.appendChild(this.name);
    }

    render(parent) {
        parent.appendChild(this.root);
        for (let treeDir of this.dirs) {
            treeDir.render(this.root);
        }
        for (let treeFile of this.files) {
            treeFile.render(this.root);
        }
    }

    toggleCollapse() {
        if (this.root.classList.contains("collapsed")) {
            this.root.classList.remove("collapsed");
        } else {
            this.root.classList.add("collapsed");
        }
    }
}

class TreeFile {
    constructor(app, name, prefix) {
        this.app = app;
        this.fullpath = prefix + name;
        this.libraryEntry = null;

        this.label = document.createElement("span");
        this.label.classList.add("tree-file-label");
        this.label.setAttribute("fullpath", this.fullpath);
        this.label.innerText = name;
        this.label.onclick = () => {this.app.selectFile(this)};
    }

    render(parent) {
        parent.appendChild(this.label);
    }

    hide() {
        this.label.classList.add("hidden");
    }

    show() {
        this.label.classList.remove("hidden");
    }
}

class LibraryView {
    constructor(app) {
        this.app = app;

        this.root = document.createElement("div");
        this.root.classList.add("library");

        this.librarySelector = new LibrarySelector(this);
        this.librarySelector.render(this.root);

        this.fields = [];
        this.libraryFields = document.createElement("div");
        this.libraryFields.classList.add("library-fields");
        this.root.appendChild(this.libraryFields);

        this.formatForm = document.createElement("form");
        this.formatForm.classList.add("library-format-form");
        this.formatInput = document.createElement("input");
        this.formatInput.classList.add("library-format-input");
        this.formatForm.onsubmit = (ev) => {ev.preventDefault(); this.formatInput.blur()};
        this.formatInput.onblur = () => {
            this.modifyLibrary(this.currentLibrary.id, {"format": this.formatInput.value});
        };
        this.formatForm.appendChild(this.formatInput);
        this.root.appendChild(this.formatForm);

        this.divEntries = document.createElement("div");
        this.divEntries.classList.add("library-tree-entries")
        this.root.appendChild(this.divEntries);

        this.linkBtn = document.createElement("input");
        this.linkBtn.classList.add("link-button");
        this.linkBtn.type = "button";
        this.linkBtn.value = "Link";
        this.linkBtn.onclick = () => {this.link()};
        this.root.appendChild(this.linkBtn);

        this.currentLibrary = null;
        this.cacheSpec = new Map();
        this.fileEntries = [];
    }

    render(parent) {
        parent.appendChild(this.root);
    }

    setLibrary(libraryId, cb) {
        let xhr = new XMLHttpRequest();
        xhr.addEventListener("load", () => {
            let spec = JSON.parse(xhr.response);
            this.currentLibrary = spec;
            this.cacheSpec.set(spec.id, spec);
            this.renderFields();
            this.renderFormat();
            cb();
        });
        xhr.open("GET", "/list_library/" + libraryId);
        xhr.send();
    }

    createLibrary(name, srcId, cb) {
        this.currentLibrary = this.cacheSpec.get(srcId);
        let nloc;
        if (this.currentLibrary.location !== null) {
            nloc = this.currentLibrary.location + name + "/";
        } else {
            nloc = name + "/";
        }

        let xhr = new XMLHttpRequest();
        xhr.addEventListener("load", () => {
            let spec = JSON.parse(xhr.response);
            spec["Library"] = [];
            spec["Record"] = [];
            this.currentLibrary.Library.push(spec);
            this.currentLibrary = spec;
            this.cacheSpec.set(spec.id, spec);
            this.renderFields();
            this.renderFormat();
            cb();
        });
        xhr.open("PUT", "/library");
        xhr.setRequestHeader('Content-Type', 'application/json');
        xhr.send(JSON.stringify({"location": nloc, "name": name, "parent_id": this.currentLibrary.id, "fields": this.currentLibrary.fields, "format": this.currentLibrary.format}));
    }

    modifyLibrary(libraryId, delta) {
        let xhr = new XMLHttpRequest();
        xhr.addEventListener("load", () => {
            let spec = JSON.parse(xhr.response);
            this.currentLibrary = {...this.currentLibrary, ...spec};
            this.cacheSpec.set(this.currentLibrary.id, this.currentLibrary);
            this.renderFields();
            this.renderFormat();
        });
        xhr.open("PATCH", "/library/" + libraryId);
        xhr.setRequestHeader('Content-Type', 'application/json');
        xhr.send(JSON.stringify(delta));
    }

    addFile(treeFile) {
        let fileEntry = new LibraryViewEntry(this.app, this, treeFile);
        this.fileEntries.push(fileEntry);
        fileEntry.attachFields(this.currentLibrary.fields);
        fileEntry.render(this.divEntries);
    }

    removeFile(treeFile) {
        let fileEntry = treeFile.libraryEntry;
        this.fileEntries.pop(this.fileEntries.indexOf(fileEntry));
        fileEntry.unrender(this.divEntries);
    }

    renderFields() {
        while (this.fields.length) {
            let fieldEntry = this.fields.pop();
            fieldEntry.unrender(this.libraryFields);
        }
        for (let field of this.currentLibrary.fields) {
            let fieldEntry = new LibraryFieldEntry(this, this.currentLibrary, field);
            this.fields.push(fieldEntry);
            fieldEntry.render(this.libraryFields);
        }
        let entryNew = new LibraryFieldNew(this, this.currentLibrary);
        this.fields.push(entryNew);
        entryNew.render(this.libraryFields);

        for (let fileEntry of this.fileEntries) {
            fileEntry.attachFields(this.currentLibrary.fields);
        }
    }

    renderFormat() {
        this.formatInput.value = this.currentLibrary.format;
    }

    link() {
        while (this.fileEntries.length) {
            let fileEntry = this.fileEntries.pop();
            fileEntry.link();
            fileEntry.unrender(this.divEntries);
        }
    }
}

class LibrarySelector {
    constructor(ctl) {
        this.ctl = ctl;

        this.root = document.createElement("div");
        this.root.classList.add("library-selector");

        this.selectorLevels = [];

        this.ctl.setLibrary(0, () => {
            this.pushLevel(this.ctl.currentLibrary);
        });
    }

    render(parent) {
        parent.appendChild(this.root);
    }

    pushLevel(spec) {
        let childLibraries = spec["Library"];
        let selectorEntry = new LibrarySelectorLevel(this, spec.id, childLibraries);
        selectorEntry.render(this.root);
        this.selectorLevels.push(selectorEntry);
    }

    selectLevel(levelSrc, targetId, targetName) {
        this.dropLevelsAfter(levelSrc);
        this.ctl.setLibrary(targetId, () => {
            this.pushLevel(this.ctl.currentLibrary);
        });
    }

    createLibrary(levelSrc, srcId, name) {
        this.dropLevelsAfter(levelSrc);
        this.ctl.createLibrary(name, srcId, () => {
            this.pushLevel(this.ctl.currentLibrary);
            levelSrc.addTarget(this.ctl.currentLibrary.id, this.ctl.currentLibrary.name);
        });
    }

    dropLevelsAfter(level) {
        let idx = this.selectorLevels.indexOf(level);
        while (this.selectorLevels.length > idx + 1) {
            let sublevel = this.selectorLevels.pop(idx + 1);
            sublevel.unrender(this.root);
        }
    }

}

class LibrarySelectorLevel {
    constructor(selector, srcId, childLibraries) {
        this.selector = selector;
        this.srcId = srcId;

        this.root = document.createElement("div");
        this.root.classList.add("library-selector-level");

        this.activeWrap = document.createElement("div");
        this.activeWrap.onclick = () => {this.togglePopup()};
        this.root.appendChild(this.activeWrap);

        this.label = document.createElement("span");
        this.label.innerText = "+";

        this.labelWrap = document.createElement("div");
        this.labelWrap.classList.add("library-selector-level-label");
        this.labelWrap.appendChild(this.label);

        this.activeWrap.appendChild(this.labelWrap);

        this.createForm = document.createElement("form");
        this.createForm.classList.add("library-selector-level-form");
        this.createInput = document.createElement("input");
        this.createInput.classList.add("library-selector-level-input");
        this.createInput.type = "text";
        this.createForm.appendChild(this.createInput);
        this.createForm.onsubmit = (ev) => {ev.preventDefault(); this.finishCreate(this.createInput.value);};
        this.createInput.onblur = (ev) => {this.hideCreate()};

        this.popup = new LibrarySelectorLevelPopup(this, childLibraries);
    }

    render(parent) {
        parent.appendChild(this.root);
    }

    unrender(parent) {
        parent.removeChild(this.root);
    }

    addTarget(libraryId, libraryName) {
        this.popup.addTarget(libraryId, libraryName);
    }

    togglePopup() {
        if (this.root.contains(this.popup.root)) {
            this.hidePopup();
        } else {
            this.showPopup();
        }
    }

    showPopup() {
        this.popup.render(this.root);
    }

    hidePopup() {
        if (this.root.contains(this.popup.root)) {
            this.popup.unrender(this.root);
        }
    }

    showCreate() {
        if (this.activeWrap.contains(this.labelWrap)) {
            this.activeWrap.removeChild(this.labelWrap);
            this.activeWrap.appendChild(this.createForm);
        }
        this.hidePopup();
        this.createInput.focus();
    }

    hideCreate() {
        if (this.activeWrap.contains(this.createForm)) {
            this.activeWrap.removeChild(this.createForm);
            this.activeWrap.appendChild(this.labelWrap);
        }
    }

    selectLevel(targetId, targetName) {
        this.hidePopup();
        this.hideCreate();
        this.label.innerText = targetName;
        this.selector.selectLevel(this, targetId, targetName);
    }

    finishCreate(targetName) {
        this.hidePopup();
        this.hideCreate();
        this.label.innerText = targetName;
        this.selector.createLibrary(this, this.srcId, targetName);
    }
}

class LibrarySelectorLevelPopup {
    constructor(level, targets) {
        this.level = level;

        this.root = document.createElement("div");
        this.root.style.setProperty("z-index", 2);
        this.root.classList.add("library-selector-level-popup");

        this.blurDummy = new BlurDummy(() => {level.hidePopup()});

        this.dynEntries = document.createElement("div");
        this.root.appendChild(this.dynEntries);

        this.entries = [];
        for (let target of targets) {
            let entry = new LibrarySelectorLevelPopupEntry(level, target.id, target.name);
            this.entries.push(entry);
            entry.render(this.dynEntries);
        }

        this.entryNew = new LibrarySelectorLevelPopupNew(level);
        this.entryNew.render(this.root);
    }

    render(parent) {
        parent.appendChild(this.root);
        this.blurDummy.set();
    }

    unrender(parent) {
        parent.removeChild(this.root);
        this.blurDummy.clear();
    }

    addTarget(targetId, targetName) {
        let entry = new LibrarySelectorLevelPopupEntry(this.level, targetId, targetName);
        this.entries.push(entry);
        entry.render(this.dynEntries);
    }
}

class LibrarySelectorLevelPopupEntry {
    constructor(level, targetId, targetName) {
        this.label = document.createElement("span");
        this.label.classList.add("library-selector-level-popup-entry");
        this.label.innerText = targetName;
        this.label.onclick = () => {level.selectLevel(targetId, targetName)};
    }

    render(parent) {
        parent.appendChild(this.label);
    }
}

class LibrarySelectorLevelPopupNew {
    constructor(level) {
        this.label = document.createElement("span");
        this.label.classList.add("library-selector-level-popup-entry");
        this.label.innerText = "+";
        this.label.onclick = () => {level.showCreate()};
    }

    render(parent) {
        parent.appendChild(this.label);
    }
}

class LibraryFieldEntry {
    constructor(selector, librarySpec, field) {
        this.selector = selector;
        this.librarySpec = librarySpec;
        this.field = field;

        this.label = document.createElement("span");
        this.label.classList.add("library-field-edit");
        this.label.innerText = field;
        this.label.onclick = () => {this.removeField()};
    }

    render(parent) {
        parent.appendChild(this.label);
    }

    unrender(parent) {
        parent.removeChild(this.label);
    }

    removeField() {
        let nfields = new Set(this.librarySpec.fields);
        nfields.delete(this.field);
        this.selector.modifyLibrary(this.librarySpec.id, {fields: [...nfields]});
    }
}

class LibraryFieldNew {
    constructor(selector, librarySpec) {
        this.selector = selector;
        this.librarySpec = librarySpec;

        this.activeWrap = document.createElement("div");
        this.activeWrap.classList.add("library-field-edit-new");

        this.labelWrap = document.createElement("div");
        this.labelWrap.classList.add("library-field-edit-label");
        this.label = document.createElement("span");
        this.label.innerText = "+";
        this.label.onclick = () => {this.showEdit()};
        this.labelWrap.appendChild(this.label)
        this.activeWrap.appendChild(this.labelWrap);

        this.addForm = document.createElement("form");
        this.addForm.classList.add("library-field-edit-form");
        this.addInput = document.createElement("input");
        this.addInput.classList.add("library-field-edit-input");
        this.addForm.appendChild(this.addInput);
        this.addForm.onsubmit = (ev) => {ev.preventDefault(); this.addField(this.addInput.value);};
        this.addInput.onblur = (ev) => {this.hideEdit()};
    }

    render(parent) {
        parent.appendChild(this.activeWrap);
    }

    unrender(parent) {
        parent.removeChild(this.activeWrap);
    }

    showEdit() {
        this.activeWrap.removeChild(this.labelWrap);
        this.activeWrap.appendChild(this.addForm);
        this.addInput.focus();
    }

    hideEdit() {
        if (this.activeWrap.contains(this.addForm)) {
            this.activeWrap.removeChild(this.addForm);
            this.activeWrap.appendChild(this.labelWrap);
        }
    }

    addField(s) {
        let nfields = [...new Set(this.librarySpec.fields.concat([s]))];
        this.label.innerText = s;
        this.hideEdit();
        this.selector.modifyLibrary(this.librarySpec.id, {fields: nfields});
    }
}

class LibraryViewEntry {
    constructor(app, ctl, treeFile) {
        this.app = app;
        this.ctl = ctl;
        this.treeFile = treeFile;
        treeFile.libraryEntry = this;

        this.root = document.createElement("div");
        this.root.classList.add("library-entry-wrap")

        this.label = document.createElement("span");
        this.label.classList.add("library-entry-label");
        this.label.innerText = treeFile.fullpath;
        console.log("treeFile", treeFile, treeFile.fullpath);
        this.label.onclick = () => {this.app.unselectFile(this.treeFile)};
        this.root.appendChild(this.label);

        this.fields = [];
        this.divFields = document.createElement("div");
        this.divFields.classList.add("library-entry-fields-wrap");
        this.root.appendChild(this.divFields);

    }

    render(parent) {
        parent.appendChild(this.root);
    }

    unrender(parent) {
        parent.removeChild(this.root);
    }

    attachFields(specFields) {
        while (this.fields.length) {
            let field = this.fields.pop();
            field.unrender(this.divFields);
        }

        for (let specField of specFields) {
            let field = new LibraryViewEntryField(specField);
            this.fields.push(field);
            field.render(this.divFields);
        }
    }

    link() {
        let fieldData = new Map();
        for (let fieldEntry of this.fields) {
            fieldData.set(fieldEntry.field, fieldEntry.input.value);
        }
        let data = {
            attributes: Object.fromEntries(fieldData),
            parent_id: this.ctl.currentLibrary.id,
            referrent: this.treeFile.fullpath,
        }
        let xhr = new XMLHttpRequest();
        xhr.open("PUT", "/record");
        xhr.setRequestHeader('Content-Type', 'application/json');
        xhr.send(JSON.stringify(data));
    }
}

class LibraryViewEntryField {
    constructor(field) {
        this.field = field

        this.root = document.createElement("div");
        this.root.classList.add("library-entry-field");

        this.label = document.createElement("span");
        this.label.innerText = field + ": ";
        this.root.appendChild(this.label);

        this.input = document.createElement("input");
        this.root.appendChild(this.input);
    }

    render(parent) {
        parent.appendChild(this.root);
    }

    unrender(parent) {
        parent.removeChild(this.root);
    }
}

class BlurDummy {
    constructor(cb) {
        this.elem = document.createElement("div");
        this.elem.style.setProperty("position", "absolute");
        this.elem.style.setProperty("top", "0px");
        this.elem.style.setProperty("left", "0px");
        this.elem.style.setProperty("height", "100%");
        this.elem.style.setProperty("width", "100%");
        this.elem.style.setProperty("z-index", "1");
        this.elem.onclick = (ev) => {this.clear(); cb();}
    }

    set() {
        document.body.appendChild(this.elem);
    }

    clear() {
        if (document.body.contains(this.elem)) {
            document.body.removeChild(this.elem);
        }
    }
}

var app = new App();
app.render("main");