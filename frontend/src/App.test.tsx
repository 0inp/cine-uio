import { render } from '@testing-library/react';
import { expect, test } from 'vitest';
import App from './App';

// Mock the DOM environment for testing
import { JSDOM } from 'jsdom';
const dom = new JSDOM('<!DOCTYPE html><html><body><div id="root"></div></body></html>');
global.document = dom.window.document;
global.window = dom.window;

test('renders learn more link', () => {
  const { getByText } = render(<App />);
  const linkElement = getByText(/learn more/i);
  expect(linkElement).toBeDefined();
});
