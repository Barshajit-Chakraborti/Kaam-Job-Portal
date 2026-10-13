/** Keep the `theme` block in sync with the inline config in templates/base.html */
module.exports = {
  content: [
    "./templates/**/*.html",
    "./*/forms.py",
    "./*/templatetags/*.py",
    "./static/js/*.js",
  ],
  theme: {
    extend: {
      colors: {
        ink: "#1C2340",
        brand: { DEFAULT: "#3B4BDB", dark: "#2C3AB8" },
        tint: "#EEF0FF",
        paper: "#F5F7FB",
        line: "#DDE1EE",
        muted: "#5B6479",
        remote: "#0E9F8E",
        onsite: "#B9620F",
      },
      fontFamily: {
        display: ['"Bricolage Grotesque"', "ui-sans-serif", "system-ui", "sans-serif"],
        sans: ['"Public Sans"', "ui-sans-serif", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};
