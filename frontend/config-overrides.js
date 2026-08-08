const TsconfigPathsPlugin = require("tsconfig-paths-webpack-plugin");

module.exports = {
  webpack: function (config) {
    // Resolve o alias @/* (TypeScript paths) via webpack resolve.
    if (!config.resolve) config.resolve = {};
    if (!Array.isArray(config.resolve.plugins)) config.resolve.plugins = [];
    config.resolve.plugins.push(new TsconfigPathsPlugin({}));

    // Substitui os plugins PostCSS do CRA pelo Tailwind v4 CSS-first.
    // CRA 5 só conhece Tailwind v3 (procura `tailwind.config.js`); no v4 não há
    // config JS e o plugin correto é `@tailwindcss/postcss`. Percorremos as
    // rules de CSS e trocamos o array `postcssOptions.plugins` por um array
    // limpo usando o plugin v4 + autoprefixer.
    const rules = config.module && config.module.rules;
    if (Array.isArray(rules)) {
      for (const rule of rules) {
        const oneOf = rule && Array.isArray(rule.oneOf) ? rule.oneOf : null;
        if (!oneOf) continue;
        for (const sub of oneOf) {
          const loaders = sub && Array.isArray(sub.use) ? sub.use : null;
          if (!loaders) continue;
          for (const loader of loaders) {
            const opts = loader && loader.options;
            const post = opts && opts.postcssOptions;
            if (!post) continue;
            post.plugins = [
              require("@tailwindcss/postcss")({}),
              require("autoprefixer")({}),
            ];
          }
        }
      }
    }

    return config;
  },
};
