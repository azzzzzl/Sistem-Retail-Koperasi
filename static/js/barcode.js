document.addEventListener("DOMContentLoaded", function () {

    // =====================================================
    // ELEMENT
    // =====================================================

    const barcodeInput =
        document.getElementById("barcode-input");

    const scanButton =
        document.getElementById("scan-barcode-btn");

    const resultContainer =
        document.getElementById("barcode-result");

    const openCameraButton =
        document.getElementById("open-camera-btn");

    const closeCameraButton =
        document.getElementById("close-camera-btn");

    const cameraContainer =
        document.getElementById("barcode-camera");


    // =====================================================
    // URL ENDPOINT DJANGO
    // =====================================================

    const scanUrl =
        scanButton?.dataset.scanUrl;


    // =====================================================
    // CAMERA STATE
    // =====================================================

    let html5QrCode = null;

    let isCameraRunning = false;

    let isProcessingScan = false;


    // =====================================================
    // DUPLICATE SCAN PROTECTION
    // =====================================================

    // Barcode terakhir yang berhasil terbaca
    let lastScannedBarcode = "";

    // Waktu terakhir barcode diproses
    let lastScanTime = 0;

    // Jeda minimal untuk barcode yang sama
    // 1500 = 1,5 detik
    const DUPLICATE_SCAN_DELAY = 1500;


    // =====================================================
    // DEBUG
    // =====================================================

    console.log("=== BARCODE JS DIMUAT ===");
    console.log("Scan URL:", scanUrl);


    // =====================================================
    // VALIDASI ELEMENT
    // =====================================================

    if (!barcodeInput) {

        console.error(
            "Element #barcode-input tidak ditemukan."
        );

        return;
    }


    if (!scanButton) {

        console.error(
            "Element #scan-barcode-btn tidak ditemukan."
        );

        return;
    }


    if (!resultContainer) {

        console.error(
            "Element #barcode-result tidak ditemukan."
        );

        return;
    }


    if (!scanUrl) {

        console.error(
            "URL scan barcode tidak ditemukan."
        );

        return;
    }


    // =====================================================
    // GET CSRF COOKIE
    // =====================================================

    function getCookie(name) {

        let cookieValue = null;

        if (
            document.cookie &&
            document.cookie !== ""
        ) {

            const cookies =
                document.cookie.split(";");


            for (
                let i = 0;
                i < cookies.length;
                i++
            ) {

                const cookie =
                    cookies[i].trim();


                if (
                    cookie.substring(
                        0,
                        name.length + 1
                    ) === name + "="
                ) {

                    cookieValue =
                        decodeURIComponent(
                            cookie.substring(
                                name.length + 1
                            )
                        );

                    break;
                }
            }
        }

        return cookieValue;
    }


    // =====================================================
    // UPDATE CART DARI RESPONSE SERVER
    // =====================================================

    function updateCartFromServer(pageHtml) {

        if (!pageHtml) {

            console.warn(
                "page_html tidak ditemukan dari server."
            );

            return;
        }


        try {

            // ---------------------------------------------
            // Buat document sementara dari HTML response
            // ---------------------------------------------

            const parser =
                new DOMParser();

            const parsedDocument =
                parser.parseFromString(
                    pageHtml,
                    "text/html"
                );


            // ---------------------------------------------
            // Cari cart baru
            // ---------------------------------------------

            const newCartContainer =
                parsedDocument.getElementById(
                    "cart-container"
                );


            // ---------------------------------------------
            // Cari cart yang sedang tampil
            // ---------------------------------------------

            const currentCartContainer =
                document.getElementById(
                    "cart-container"
                );


            if (!newCartContainer) {

                console.warn(
                    "Element #cart-container tidak ditemukan pada response server."
                );

                return;
            }


            if (!currentCartContainer) {

                console.warn(
                    "Element #cart-container tidak ditemukan pada halaman saat ini."
                );

                return;
            }


            // ---------------------------------------------
            // Ganti cart lama dengan cart baru
            // ---------------------------------------------

            currentCartContainer.replaceWith(
                newCartContainer
            );


            console.log(
                "Cart berhasil diperbarui tanpa reload."
            );

        } catch (error) {

            console.error(
                "Gagal memperbarui cart:",
                error
            );
        }
    }


    // =====================================================
    // RESET CAMERA UI
    // =====================================================

    function resetCameraUI() {

        if (cameraContainer) {

            cameraContainer.style.display =
                "none";

            cameraContainer.innerHTML =
                "";
        }


        if (closeCameraButton) {

            closeCameraButton.style.display =
                "none";
        }


        if (openCameraButton) {

            openCameraButton.style.display =
                "inline-block";
        }


        isCameraRunning = false;
    }


    // =====================================================
    // STOP CAMERA
    // =====================================================

    async function cleanupCamera() {

        console.log(
            "Menghentikan kamera..."
        );


        if (!html5QrCode) {

            resetCameraUI();

            return;
        }


        try {

            if (isCameraRunning) {

                await html5QrCode.stop();

                console.log(
                    "Kamera berhasil dihentikan."
                );
            }

        } catch (error) {

            console.warn(
                "Kamera sudah tidak aktif:",
                error
            );
        }


        try {

            await html5QrCode.clear();

            console.log(
                "Scanner berhasil dibersihkan."
            );

        } catch (error) {

            console.warn(
                "Scanner gagal dibersihkan:",
                error
            );
        }


        html5QrCode = null;

        isCameraRunning = false;


        if (cameraContainer) {

            cameraContainer.innerHTML =
                "";
        }


        resetCameraUI();
    }


    // =====================================================
    // PROCESS BARCODE
    // =====================================================

    async function processBarcode(barcode) {

        barcode =
            String(barcode).trim();


        // ---------------------------------------------
        // VALIDASI BARCODE
        // ---------------------------------------------

        if (!barcode) {

            resultContainer.innerHTML =
                "<div>Barcode wajib diisi.</div>";

            return false;
        }


        console.log(
            "Memproses barcode:",
            barcode
        );


        console.log(
            "POST ke:",
            scanUrl
        );


        // ---------------------------------------------
        // CSRF TOKEN
        // ---------------------------------------------

        const csrfToken =
            getCookie("csrftoken");


        if (!csrfToken) {

            resultContainer.innerHTML =
                "<div>CSRF token tidak ditemukan. Silakan refresh halaman.</div>";

            return false;
        }


        try {

            // =================================================
            // REQUEST KE DJANGO
            // =================================================

            const response =
                await fetch(
                    scanUrl,
                    {
                        method: "POST",

                        headers: {

                            "Content-Type":
                                "application/x-www-form-urlencoded; charset=UTF-8",

                            "X-CSRFToken":
                                csrfToken,

                            "X-Requested-With":
                                "XMLHttpRequest"
                        },

                        body:
                            new URLSearchParams({
                                barcode:
                                    barcode
                            })
                        }
                    );


            console.log(
                "Status response:",
                response.status
            );


            // =================================================
            // CEK RESPONSE
            // =================================================

            const data =
                await response.json();


            console.log(
                "Response server:",
                data
            );


            // =================================================
            // BARCODE GAGAL DIPROSES
            // =================================================

            if (!data.success) {

                resultContainer.innerHTML = `
                    <div>
                        ${data.message ||
                        "Barcode tidak dapat diproses."}
                    </div>
                `;


                // Kosongkan input manual
                barcodeInput.value = "";


                // Kamera tetap menyala
                return false;
            }


            // =================================================
            // BARCODE BERHASIL
            // =================================================

            const product =
                data.product;


            resultContainer.innerHTML = `
                <div>
                    <strong>
                        ${product.name}
                    </strong>

                    <br>

                    SKU:
                    ${product.sku}

                    <br>

                    Barcode:
                    ${product.barcode}

                    <br>

                    Harga:
                    ${product.selling_price}

                    <br>

                    Stok:
                    ${product.stock}

                    <br>

                    Quantity di keranjang:
                    ${data.quantity}
                </div>
            `;


            // ---------------------------------------------
            // KOSONGKAN INPUT
            // ---------------------------------------------

            barcodeInput.value = "";


            // =================================================
            // UPDATE CART REALTIME
            // =================================================
            //
            // Server mengirim HTML terbaru dari index.html.
            //
            // Kita hanya mengambil:
            //
            // #cart-container
            //
            // kemudian mengganti cart lama.
            //
            // Kamera tidak ikut diganti sehingga tetap menyala.
            // =================================================

            if (data.page_html) {

                updateCartFromServer(
                    data.page_html
                );

            } else {

                console.warn(
                    "Response tidak memiliki page_html. Cart tidak diperbarui."
                );
            }


            // ---------------------------------------------
            // JANGAN RELOAD HALAMAN
            // ---------------------------------------------
            //
            // Jangan gunakan:
            //
            // window.location.reload();
            //
            // Karena reload akan mematikan kamera.
            // ---------------------------------------------


            return true;


        } catch (error) {

            console.error(
                "Error saat menghubungi server:",
                error
            );


            resultContainer.innerHTML =
                "<div>Terjadi kesalahan saat menghubungi server.</div>";


            barcodeInput.value = "";


            // Kamera tetap menyala
            return false;
        }
    }


    // =====================================================
    // SCAN MANUAL
    // =====================================================

    scanButton.addEventListener(
        "click",
        async function () {

            console.log(
                "Tombol Scan Barcode diklik."
            );


            // -----------------------------------------
            // Jangan proses jika masih ada request
            // -----------------------------------------

            if (isProcessingScan) {

                console.log(
                    "Masih memproses barcode sebelumnya."
                );

                return;
            }


            const barcode =
                barcodeInput.value.trim();


            // -----------------------------------------
            // Validasi
            // -----------------------------------------

            if (!barcode) {

                resultContainer.innerHTML =
                    "<div>Barcode wajib diisi.</div>";

                return;
            }


            // -----------------------------------------
            // Proses barcode
            // -----------------------------------------

            isProcessingScan =
                true;


            try {

                await processBarcode(
                    barcode
                );

            } finally {

                isProcessingScan =
                    false;
            }
        }
    );


    // =====================================================
    // OPEN CAMERA
    // =====================================================

    if (openCameraButton) {

        openCameraButton.addEventListener(
            "click",
            async function () {

                console.log(
                    "Tombol Scan dengan Kamera diklik."
                );


                // -----------------------------------------
                // Jika kamera sudah menyala
                // -----------------------------------------

                if (isCameraRunning) {

                    console.log(
                        "Kamera sudah menyala."
                    );

                    return;
                }


                // -----------------------------------------
                // RESET INPUT
                // -----------------------------------------

                barcodeInput.value = "";

                resultContainer.innerHTML = "";


                // -----------------------------------------
                // CEK LIBRARY
                // -----------------------------------------

                if (
                    typeof Html5Qrcode ===
                    "undefined"
                ) {

                    console.error(
                        "Html5Qrcode tidak ditemukan."
                    );


                    resultContainer.innerHTML =
                        "<div>Library scanner kamera tidak tersedia.</div>";

                    return;
                }


                // -----------------------------------------
                // TAMPILKAN CAMERA CONTAINER
                // -----------------------------------------

                if (cameraContainer) {

                    cameraContainer.innerHTML =
                        "";

                    cameraContainer.style.display =
                        "block";
                }


                // -----------------------------------------
                // TAMPILKAN TOMBOL TUTUP
                // -----------------------------------------

                if (closeCameraButton) {

                    closeCameraButton.style.display =
                        "inline-block";
                }


                // -----------------------------------------
                // SEMBUNYIKAN TOMBOL BUKA
                // -----------------------------------------

                openCameraButton.style.display =
                    "none";


                // -----------------------------------------
                // RESET PROCESSING
                // -----------------------------------------

                isProcessingScan =
                    false;


                // -----------------------------------------
                // RESET DUPLICATE SCAN
                // -----------------------------------------

                lastScannedBarcode = "";

                lastScanTime = 0;


                // -----------------------------------------
                // BUAT SCANNER
                // -----------------------------------------

                try {

                    html5QrCode =
                        new Html5Qrcode(
                            "barcode-camera"
                        );


                    // =====================================
                    // START CAMERA
                    // =====================================

                    await html5QrCode.start(

                        {
                            facingMode:
                                "environment"
                        },

                        {
                            fps: 10,

                            qrbox: {
                                width: 250,
                                height: 150
                            }
                        },


                        // =================================
                        // BARCODE BERHASIL DIBACA
                        // =================================

                        async function (
                            decodedText
                        ) {

                            const scannedBarcode =
                                String(
                                    decodedText
                                ).trim();


                            // ---------------------------------
                            // Validasi
                            // ---------------------------------

                            if (!scannedBarcode) {

                                return;
                            }


                            // =================================
                            // CEGAH DUPLIKAT SCAN
                            // =================================

                            const now =
                                Date.now();


                            if (
                                scannedBarcode ===
                                    lastScannedBarcode
                                &&
                                now -
                                    lastScanTime <
                                    DUPLICATE_SCAN_DELAY
                            ) {

                                console.log(
                                    "Scan diabaikan karena barcode yang sama baru saja diproses:",
                                    scannedBarcode
                                );


                                return;
                            }


                            // =================================
                            // CEGAH REQUEST BERSAMAAN
                            // =================================

                            if (
                                isProcessingScan
                            ) {

                                console.log(
                                    "Masih memproses scan sebelumnya."
                                );


                                return;
                            }


                            // =================================
                            // SIMPAN BARCODE TERAKHIR
                            // =================================

                            lastScannedBarcode =
                                scannedBarcode;


                            lastScanTime =
                                now;


                            // =================================
                            // MULAI PROCESSING
                            // =================================

                            isProcessingScan =
                                true;


                            console.log(
                                "================================="
                            );


                            console.log(
                                "Barcode kamera terbaca:",
                                scannedBarcode
                            );


                            console.log(
                                "Memproses barcode..."
                            );


                            try {

                                await processBarcode(
                                    scannedBarcode
                                );

                            } catch (error) {

                                console.error(
                                    "Error saat memproses barcode:",
                                    error
                                );

                            } finally {

                                // ---------------------------------
                                // Scanner TETAP MENYALA
                                // ---------------------------------

                                isProcessingScan =
                                    false;


                                console.log(
                                    "Kamera tetap menyala."
                                );


                                console.log(
                                    "================================="
                                );
                            }
                        },


                        // =================================
                        // ERROR PEMBACAAN
                        // =================================

                        function (errorMessage) {

                            /*
                             * Error seperti:
                             *
                             * QR code parse error
                             * Barcode tidak terbaca
                             *
                             * adalah hal normal ketika kamera
                             * sedang mencari barcode.
                             *
                             * Jadi tidak perlu ditampilkan
                             * kepada user.
                             */
                        }
                    );


                    // -----------------------------------------
                    // CAMERA BERHASIL MENYALA
                    // -----------------------------------------

                    isCameraRunning =
                        true;


                    console.log(
                        "Kamera berhasil dibuka."
                    );


                    console.log(
                        "Kamera akan tetap menyala sampai tombol Tutup Kamera ditekan."
                    );


                } catch (error) {

                    console.error(
                        "Gagal membuka kamera:",
                        error
                    );


                    // -----------------------------------------
                    // Bersihkan jika gagal
                    // -----------------------------------------

                    await cleanupCamera();


                    resultContainer.innerHTML =
                        "<div>Kamera tidak dapat dibuka. Pastikan izin kamera diberikan.</div>";


                    barcodeInput.value = "";


                    isProcessingScan =
                        false;
                }
            }
        );
    }


    // =====================================================
    // CLOSE CAMERA
    // =====================================================

    if (closeCameraButton) {

        closeCameraButton.addEventListener(
            "click",
            async function () {

                console.log(
                    "Tombol Tutup Kamera diklik."
                );


                // -----------------------------------------
                // HENTIKAN KAMERA
                // -----------------------------------------

                await cleanupCamera();


                // -----------------------------------------
                // RESET INPUT
                // -----------------------------------------

                barcodeInput.value = "";


                // -----------------------------------------
                // RESET HASIL
                // -----------------------------------------

                resultContainer.innerHTML =
                    "";


                // -----------------------------------------
                // RESET PROCESSING
                // -----------------------------------------

                isProcessingScan =
                    false;


                // -----------------------------------------
                // RESET DUPLICATE PROTECTION
                // -----------------------------------------

                lastScannedBarcode =
                    "";

                lastScanTime =
                    0;


                console.log(
                    "Kamera ditutup."
                );
            }
        );
    }

});