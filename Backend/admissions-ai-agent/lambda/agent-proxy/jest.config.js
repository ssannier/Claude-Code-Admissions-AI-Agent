module.exports = {
  testEnvironment: 'node',
  coverageDirectory: 'coverage',
  collectCoverageFrom: [
    'index.js',
    '!jest.config.js'
  ],
  testMatch: [
    '**/__tests__/**/*.test.js'
  ],
  verbose: true
};
