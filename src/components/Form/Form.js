import React from "react";
import { useWeb3React } from '@web3-react/core';
//import {ethers} from 'ethers'
import styles from './Form.module.css';

export default function Form(props) {

  return (
    <div className={styles.container}>
      <button onClick={() => props.changePage("home")} className={styles.backButton}>← Go Back</button>
      <h1>Launch your Lens astrological profile </h1>
      <form>
        <div className={styles.inputContainer}>
          <input type="text" id="birthplace" name="birthplace" placeholder="Place of birth"/>
        </div>
        <div className={styles.inputContainer}>
          <input type="text" id="date" name="date" placeholder="MM / DD / YY"/>
        </div>
        <div className={styles.inputContainer}>
          <input type="text" id="time" name="time" placeholder="HH : MM"/>
        </div>
      </form>
    </div>
)};
