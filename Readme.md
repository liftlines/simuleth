4. Open a web browser and navigate to `http://localhost:5000` or site address

## Usage

1. Enter the validator balance in ETH
2. Select your execution and consensus clients
3. Choose between "Node goes offline" or "Double Signing" scenarios
4. Fill in the required information for the chosen scenario
5. Click "Calculate Penalty" to see the results

## Scenarios

### Node goes offline
This scenario calculates penalties for a validator that goes offline for a specified duration. It considers:
- Inactivity penalties
- Missed attestation rewards

### Double Signing
This scenario estimates penalties for a validator that signs two different blocks in the same slot. It includes:
- Base slashing penalty
- Correlated slashing penalty (optional)
- Long-term penalty estimate

## Technical Details

- Built with Flask (Python web framework)
- Uses NES.css for retro-style UI
- Calculations based on Ethereum Deneb specifications

## Contributing

We welcome contributions to simuleth! Please read our [contributing guidelines](CONTRIBUTING.md) before submitting pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Ethereum Foundation for the validator penalty specifications
- [NES.css](https://nostalgic-css.github.io/NES.css/) for the retro styling

## Disclaimer

This tool provides estimates based on current Ethereum specifications. Always refer to the official Ethereum documentation for the most up-to-date and accurate information. The calculations are simplified and may not account for all factors in real-world scenarios.

## Future Improvements

- Add more scenario types
- Implement real-time data fetching for network statistics
- Improve accuracy of long-term penalty estimates
- Add visualizations for penalty breakdowns

## Contact

For questions or feedback, please open an issue on this repository or contact the maintainers directly.

---

Remember to keep your validator keys secure and never share them. Happy validating!
