import modal

pricer = modal.Function.from_name("pricer-service", "price")
print(pricer.remote("Quadcast HyperX condenser mic, connects via usb-c to your computer for crystal clear audio"))