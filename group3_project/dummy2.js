// Special Characters Test File

// Quotes
const singleQuote = 'This is a string with a single quote (\') inside.';
const doubleQuote = "This is a string with a double quote (\") inside.";
const backtick = `This is a template literal with "quotes" and 'single quotes'.`;

// Escape sequences
const escapeChars = "Newline:\nTab:\tBackslash:\\ Double Quote:\" Single Quote:\'";

// Brackets and braces
const obj = {
    key1: "value1",
    key2: "value2",
    nested: {
        arr: [1, 2, 3],
        func: () => {
            console.log("Inside an arrow function!");
        }
    }
};

// Special regex characters
const regex = /[\[\]{}()*+?.\\^$|]/g;

// Unicode characters
const unicode = "Special: 𝒜, Non-ASCII: ñ, ç, 你好";

// HTML-like syntax (common in JS frameworks)
const htmlSnippet = `<div class="test">Content with <span>special characters</span></div>`;

// Dollar sign & template literals
const variable = "value";
const templateLiteral = `This is a ${variable} inside a template string.`;

// Comments with special characters
// This is a comment with: !@#$%^&*()_+-=[]{}|;:'",.<>?/`~

// Function with special syntax
function testFunction(param = "default") {
    console.log(`Parameter: ${param}`);
}

// Call everything
testFunction();
obj.nested.func();
console.log(singleQuote, doubleQuote, backtick, escapeChars, regex, unicode, htmlSnippet, templateLiteral);