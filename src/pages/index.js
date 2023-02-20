import React, { useState, useEffect, useCallback } from "react";
import { useWeb3React } from '@web3-react/core';
import { InjectedConnector } from '@web3-react/injected-connector';
import { switch2Polygon} from '../utils/networkConnect.js';
import Head from 'next/head';
import Background from '../components/Background/Background.js';
import Header from '../components/Header/Header.js';
import Home from '../components/Home/Home.js';
import Form from '../components/Form/Form.js';
import Button from '../components/Buttons/Button.js';
import Modal from '../components/Modal/Modal.js';
import Footer from '../components/Footer/Footer.js';
import styles from '@/styles/Index.module.css';
// logos
import ethereum_icon from '../icons/ethereum.svg';
import wallet_connect_icon from '../icons/wallet_connect.svg';



export default function Index(props) {
  const [showModal, setShowModal] = useState(false);
  // TODO: change to enum
  const [page, setPage] = useState("home");

  const wrapperSetPage = useCallback(page => {
    setPage(page);
  }, [setPage]);

  return (
    <>
      <Head>
        <title>Astrace X Lens</title>
        <meta name="description" content="Launch your Lens astrological profile" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </Head>
      <Background />
      <div className={styles.main}>
        <Header showWallet={false} page={"home"}/>
        {page == "home" && <Home changePage={wrapperSetPage} />}
        {page == "form" && <Form changePage={wrapperSetPage} />}
        <Footer/>
      </div>
    </>
  )
};
